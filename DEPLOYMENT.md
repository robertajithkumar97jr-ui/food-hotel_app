# EC2 deployment guide

This example uses Ubuntu 24.04, a Linux Jenkins agent and a public Docker Hub repository. Orders do not collect online payments. Use a fresh database: an older database may still contain the insecure demo admin account.

## Architecture

Git push → Jenkins build and test → Docker Hub → Ansible over SSH → EC2 Docker container → SQLite volume. FastAPI serves the API and React frontend. Nginx terminates HTTPS and proxies to the container on localhost.

## 1. Prepare EC2

Assign an Elastic IP and point your domain's DNS A record to it. In the security group allow TCP 22 only from administrator and Jenkins IP addresses, and TCP 80 and 443 from the internet. Connect from your workstation:

```bash
chmod 400 ~/restaurant-ec2.pem
ssh -i ~/restaurant-ec2.pem ubuntu@EC2_PUBLIC_IP
```

On EC2 install Docker using https://docs.docker.com/engine/install/ubuntu/ then run:

```bash
sudo systemctl enable --now docker
sudo docker run --rm hello-world
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

Generate a secret using `openssl rand -hex 32`. Run `sudo nano /etc/ajith-food-corner.env` and add your own values with no spaces around `=`:

```text
JWT_SECRET=YOUR_LONG_RANDOM_SECRET
ADMIN_EMAIL=you@example.com
ADMIN_PASSWORD=YOUR_STRONG_PASSWORD
```

Run `sudo chmod 600 /etc/ajith-food-corner.env`. The first startup creates the admin only if no admin exists; changing this file later does not change an existing account. Never commit secrets or keys.

## 2. Configure Git and Jenkins

Change `ansible_host` in `ansible/inventory.ini` to your EC2 IP, and set `IMAGE_REPO` in `Jenkinsfile` to your lowercase Docker Hub repository, such as `myuser/ajith-food-corner`. Create the public repository on Docker Hub. Commit and push the project:

```bash
git status
git add .
git commit -m "Configure deployment"
git push origin main
```

Initialize Git and add your remote first if needed. On a trusted Linux Jenkins agent, install Git, Docker, Python and Ansible. Verify `git --version`, `docker version`, and `ansible --version`. The Jenkins user needs Docker access, which is root-equivalent. Install Jenkins Pipeline, Git, SSH Agent and Credentials Binding plugins.

Create Jenkins credentials: `dockerhub` as username/password (Docker Hub username and access token), and `ec2-ssh` as SSH username/private key (username `ubuntu` and the EC2 private key). Verify the EC2 SSH host fingerprint independently and add its public host key to the Jenkins agent user's `~/.ssh/known_hosts`. Ensure the EC2 user has passwordless sudo. Test from the agent:

```bash
ansible -i ansible/inventory.ini restaurant -m ping --private-key /secure/path/restaurant-ec2.pem
```

## 3. Run the pipeline

Create a Jenkins Pipeline job, choose Pipeline script from SCM, enter the Git repository and branch, and use `Jenkinsfile` as the script path. Select Build Now. The pipeline builds React and FastAPI, runs the API test, pushes a build-number tag, and runs Ansible to pull and start the image. Configure a Git webhook or Jenkins SCM polling after the manual run succeeds. Jenkins must reach Git, Docker Hub and EC2. Private registry images require EC2 registry authentication; this example uses a public image.

The playbook preserves the `ajith_data` Docker volume and checks `/api/menu`. It replaces the running container, causing downtime, and does not automatically roll back. To restore an earlier tag from the agent:

```bash
IMAGE_NAME=myuser/ajith-food-corner:PREVIOUS_BUILD_NUMBER ansible-playbook -i ansible/inventory.ini ansible/deploy.yml --private-key /secure/path/restaurant-ec2.pem
```

## 4. Verify and enable HTTPS

On EC2:

```bash
sudo docker ps
sudo docker logs --tail 100 ajith-food-corner
curl -f http://127.0.0.1:8000/api/menu
sudo docker volume inspect ajith_data
```

For private browser testing, run `ssh -i ~/restaurant-ec2.pem -L 8000:127.0.0.1:8000 ubuntu@EC2_PUBLIC_IP` on your workstation and visit `http://127.0.0.1:8000` while it remains connected.

For HTTPS, create `/etc/nginx/sites-available/restaurant` with `sudo nano`, substituting your domain:

```nginx
server {
    listen 80;
    server_name restaurant.example.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/restaurant /etc/nginx/sites-enabled/restaurant
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d restaurant.example.com
sudo certbot renew --dry-run
curl -f https://restaurant.example.com/api/menu
```

DNS must point to EC2 and port 80 must be reachable for certificate issuance. Test login, all order types, tracking and kitchen updates. Diagnose with `sudo journalctl -u nginx -n 100`, `sudo nginx -t`, and the Docker logs above.

## 5. Operations

This prototype needs a security review and full application testing before handling real customer data. SQLite in a Docker volume is not a backup: use SQLite's backup API or `.backup`, copy backups off EC2, and test restoration. This is one server, not high availability. Sales reports show order totals, not verified payments.
