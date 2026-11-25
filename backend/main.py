import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///./ajith_food_corner.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
SECRET = os.getenv("JWT_SECRET", "change-this-secret-for-production")
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True); name = Column(String); email = Column(String, unique=True); password = Column(String); is_admin = Column(Boolean, default=False)
class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True); name = Column(String); tamil_name = Column(String); category = Column(String); price = Column(Float); description = Column(String); veg = Column(Boolean); available = Column(Boolean, default=True)
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True); user_id = Column(Integer, ForeignKey("users.id")); order_type = Column(String); address = Column(String); total = Column(Float); status = Column(String, default="Order received"); payment_status = Column(String, default="Pending"); created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("OrderItem", cascade="all, delete-orphan")
class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True); order_id = Column(Integer, ForeignKey("orders.id")); menu_item_id = Column(Integer); name = Column(String); quantity = Column(Integer); price = Column(Float)

class Register(BaseModel): name: str; email: EmailStr; password: str
class Login(BaseModel): email: EmailStr; password: str
class CartLine(BaseModel): id: int; quantity: int
class Checkout(BaseModel): items: list[CartLine]; order_type: str; address: str = ""
class StatusUpdate(BaseModel): status: str

app = FastAPI(title="Ajith Food Corner API")
def db():
    session = SessionLocal()
    try: yield session
    finally: session.close()
def token(user): return jwt.encode({"sub": str(user.id), "admin": user.is_admin, "exp": datetime.utcnow()+timedelta(days=7)}, SECRET, algorithm="HS256")
def current(request: Request, session: Session = Depends(db)):
    auth = request.headers.get("Authorization", "")
    try: data = jwt.decode(auth.replace("Bearer ", ""), SECRET, algorithms=["HS256"]); user = session.get(User, int(data["sub"]))
    except (JWTError, ValueError): raise HTTPException(401, "Please sign in")
    if not user: raise HTTPException(401, "Please sign in")
    return user
def admin(user: User = Depends(current)):
    if not user.is_admin: raise HTTPException(403, "Admin access required")
    return user
def serialize_menu(x): return {"id":x.id,"name":x.name,"tamilName":x.tamil_name,"category":x.category,"price":x.price,"description":x.description,"veg":x.veg,"available":x.available}
def serialize_order(o): return {"id":o.id,"type":o.order_type,"address":o.address,"total":o.total,"status":o.status,"paymentStatus":o.payment_status,"createdAt":o.created_at.isoformat(),"items":[{"name":i.name,"quantity":i.quantity,"price":i.price} for i in o.items]}

@app.on_event("startup")
def seed():
    Base.metadata.create_all(engine)
    s=SessionLocal()
    admin_email, admin_password = os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
    if admin_email and admin_password and not s.query(User).filter_by(is_admin=True).first():
        s.add(User(name="Ajith Admin",email=admin_email,password=pwd.hash(admin_password),is_admin=True))
    if not s.query(MenuItem).first():
        data=[("Chettinad Chicken","செட்டிநாடு சிக்கன்","Starters",289,"Fiery roasted chicken in Chettinad spices",False),("Paneer Tikka","பனீர் டிக்கா","Starters",229,"Charred cottage cheese, royal spice rub",True),("Mutton Biryani","மட்டன் பிரியாணி","Biryani",349,"Aromatic seeraga samba rice and tender mutton",False),("Veg Dum Biryani","வெஜ் தம் பிரியாணி","Biryani",219,"Fragrant vegetables and saffron rice",True),("Fish Fry","மீன் வறுவல்","Mains",259,"Coastal fish, turmeric and curry leaf",False),("Kothu Parotta","கொத்து பரோட்டா","Mains",189,"Flaky parotta tossed with masala",True),("Elaneer Payasam","இளநீர் பாயசம்","Desserts",129,"Tender coconut milk pudding",True),("Filter Coffee","ஃபில்டர் காபி","Beverages",79,"Traditional South Indian coffee",True)]
        s.add_all([MenuItem(name=a,tamil_name=b,category=c,price=d,description=e,veg=f) for a,b,c,d,e,f in data])
    s.commit(); s.close()

@app.post("/api/auth/register")
def register(body:Register, s:Session=Depends(db)):
    if s.query(User).filter_by(email=body.email).first(): raise HTTPException(400,"Email already registered")
    u=User(name=body.name,email=body.email,password=pwd.hash(body.password)); s.add(u);s.commit();s.refresh(u);return {"token":token(u),"name":u.name,"admin":False}
@app.post("/api/auth/login")
def login(body:Login,s:Session=Depends(db)):
    u=s.query(User).filter_by(email=body.email).first()
    if not u or not pwd.verify(body.password,u.password): raise HTTPException(401,"Invalid email or password")
    return {"token":token(u),"name":u.name,"admin":u.is_admin}
@app.get("/api/menu")
def menu(s:Session=Depends(db)): return [serialize_menu(x) for x in s.query(MenuItem).filter_by(available=True).all()]
@app.post("/api/orders")
def checkout(body:Checkout,user:User=Depends(current),s:Session=Depends(db)):
    if body.order_type not in ["Delivery","Pickup","Dine-in"] or not body.items: raise HTTPException(400,"Add items and choose an order type")
    products=[]; total=0
    for line in body.items:
        item=s.get(MenuItem,line.id)
        if not item or not item.available or line.quantity<1: raise HTTPException(400,"Invalid menu item")
        products.append((item,line.quantity)); total+=item.price*line.quantity
    o=Order(user_id=user.id,order_type=body.order_type,address=body.address,total=total,payment_status="Not collected")
    s.add(o);s.flush()
    for item,q in products:s.add(OrderItem(order_id=o.id,menu_item_id=item.id,name=item.name,quantity=q,price=item.price))
    s.commit();s.refresh(o);return serialize_order(o)
@app.get("/api/orders/me")
def my_orders(user:User=Depends(current),s:Session=Depends(db)): return [serialize_order(o) for o in s.query(Order).filter_by(user_id=user.id).order_by(Order.id.desc()).all()]
@app.get("/api/admin/orders")
def all_orders(_:User=Depends(admin),s:Session=Depends(db)): return [serialize_order(o) for o in s.query(Order).order_by(Order.id.desc()).all()]
@app.patch("/api/admin/orders/{order_id}")
def update_order(order_id:int,body:StatusUpdate,_:User=Depends(admin),s:Session=Depends(db)):
    o=s.get(Order,order_id)
    if not o: raise HTTPException(404,"Order not found")
    o.status=body.status;s.commit();s.refresh(o);return serialize_order(o)
@app.get("/api/admin/report")
def report(_:User=Depends(admin),s:Session=Depends(db)):
    orders=s.query(Order).all(); return {"orders":len(orders),"revenue":round(sum(o.total for o in orders),2),"active":sum(o.status not in ["Delivered","Completed"] for o in orders),"recent":[serialize_order(o) for o in sorted(orders,key=lambda x:x.id,reverse=True)[:5]]}

DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST,"assets")), name="assets")
    @app.get("/{path:path}")
    def spa(path:str): return FileResponse(os.path.join(DIST,"index.html"))
