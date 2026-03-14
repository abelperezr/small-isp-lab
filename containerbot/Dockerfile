FROM python:3.11-slim


RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    openssh-server \
    sshpass \
    iputils-ping \
    dnsutils \
    curl \
    jq \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/sshd \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/#KbdInteractiveAuthentication.*/KbdInteractiveAuthentication no/' /etc/ssh/sshd_config

WORKDIR /app

# -- Python dependencies --
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -- Ansible --
RUN pip install --no-cache-dir ansible-core

# -- Application code --
COPY bot.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# -- Script and playbook directories --
RUN mkdir -p /app/scripts /app/ansible


# Make all scripts executable
RUN find /app/scripts -type f \( -name '*.sh' -o -name '*.py' \) -exec chmod +x {} +

# -- Runtime --
RUN mkdir -p /app/logs
ENV PYTHONUNBUFFERED=1
ENV SCRIPTS_DIR=/app/scripts
ENV ANSIBLE_DIR=/app/ansible
ENV CONFIG_FILE=/app/config.yaml

ENTRYPOINT ["/app/entrypoint.sh"]
