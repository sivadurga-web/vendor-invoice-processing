# Build Stage
FROM node:18-bullseye
WORKDIR /app
# Install dependencies and clone repositories
RUN apt-get update && apt-get install -y git  \
    && git clone https://github.com/cashfree/cashfree-mcp.git \
    && git clone https://github.com/sivadurga-web/vendor-invoice-processor-chat \ 
    && cd /app/cashfree-mcp \
    && git checkout disable-endpoints

# Install runtime dependencies
RUN apt-get update && apt-get install -y python3 python3-pip ca-certificates \
    && pip install uv \
    && update-ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
# Create user and group
RUN addgroup --system cfgrp && adduser --system --ingroup cfgrp cf
WORKDIR /app

# Copy files from the builder stage and the current directory
COPY ./ /app

# Set permissions for the cf user
RUN chown -R cf:cfgrp /app \
    && chmod +x /app/start.sh \
    && chown -R cf:cfgrp /app/vendor-invoice-processor-chat \
    && mkdir -p /app/vendor-invoice-processor-chat/node_modules \
    && chown -R cf:cfgrp /app/vendor-invoice-processor-chat/node_modules
RUN cd /app/cashfree-mcp && npm install
RUN cd /app/vendor-invoice-processor-chat && npm install

# Switch to the cf user
USER cf
# Expose the application port
EXPOSE 8080
# Set the entrypoint to the start script
ENTRYPOINT ["sh", "/app/start.sh"]
