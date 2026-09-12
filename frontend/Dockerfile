FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json ./
RUN npm install

FROM node:22-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=
ARG NEXT_PUBLIC_COPILOTKIT_AGENT_ID=truesource_guardian
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=${NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL}
ENV NEXT_PUBLIC_COPILOTKIT_AGENT_ID=${NEXT_PUBLIC_COPILOTKIT_AGENT_ID}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=
ENV NEXT_PUBLIC_COPILOTKIT_AGENT_ID=truesource_guardian
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
