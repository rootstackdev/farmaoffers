FROM odoo:18.0

USER root

# Ajuste de repos por buster EOL (si usas apt)
RUN set -eux; \
    sed -i 's|deb.debian.org/debian|archive.debian.org/debian|g' /etc/apt/sources.list; \
    sed -i 's|security.debian.org/debian-security|archive.debian.org/debian-security|g' /etc/apt/sources.list || true; \
    printf 'Acquire::Check-Valid-Until "false";\n' > /etc/apt/apt.conf.d/99no-check-valid; \
    apt-get -o Acquire::Check-Valid-Until=false update; \
    apt-get install -y --no-install-recommends python3-pip python3-setuptools build-essential libssl-dev libffi-dev python3-dev; \
    rm -rf /var/lib/apt/lists/*

COPY ./libs/intfiscal-python-library-main.zip /tmp/intfiscal-python-library-main.zip
RUN pip3 install --no-cache-dir --break-system-packages /tmp/intfiscal-python-library-main.zip

USER odoo