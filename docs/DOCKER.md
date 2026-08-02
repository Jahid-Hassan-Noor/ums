# Portal Docker Setup

The Portal app runs as a four-service Compose project named `portal`:

- `portal_backend`
- `portal_frontend`
- `portal_postgresql`
- `portal_nginx`

All services now run inside the same Compose project and communicate on the default Compose network.

## Files

- `docker-compose.yml` defines the `portal` stack.
- `docker-compose.override.yml` is loaded automatically for local development.
- `.env` contains local runtime secrets and generated portal database credentials.
- `.env.example` is the safe template.
- `deploy/nginx/portal.local.conf` routes nginx traffic to the portal containers.
- `backend/Dockerfile` builds the Django API image.
- `frontend/Dockerfile` builds the Next.js standalone image.

## Docker Hub Images

Set these values in `.env` before building images you want to push:

```sh
DOCKERHUB_NAMESPACE=your-dockerhub-username
IMAGE_TAG=latest
```

The Compose image names become:

- `${DOCKERHUB_NAMESPACE}/portal-backend:${IMAGE_TAG}`
- `${DOCKERHUB_NAMESPACE}/portal-frontend:${IMAGE_TAG}`

Build the Docker Hub-tagged images:

```sh
docker compose -f docker-compose.yml build
```

Push both images:

```sh
docker login
docker compose -f docker-compose.yml push
```

## Daily Commands

Local development is the default. Compose automatically merges
`docker-compose.override.yml`, mounts both source trees, and runs the Django and
Next.js development servers:

```sh
docker compose up
```

Open the app while developing at:

- `http://127.0.0.1/` through nginx
- `http://127.0.0.1:3000/` for the Next.js dev server directly

Python, TypeScript, CSS, and other source edits are read from the bind mounts and
do not require an image rebuild. Rebuild only after changing a Dockerfile or
backend dependencies, using normal Docker layer caching:

```sh
docker compose up -d --build backend
docker compose up -d --build frontend
```

Frontend dependencies live in a separate development `node_modules` volume.
Refresh that volume after changing `package.json` or `package-lock.json`:

```sh
docker compose stop frontend
docker compose run --rm frontend npm ci
docker compose up -d frontend
```

Production mode must explicitly use only the main Compose file so the local
development override is not loaded:

```sh
docker compose -f docker-compose.yml up -d --build
```

Run backend management commands inside the Docker backend container:

```sh
docker compose exec backend python manage.py check
docker compose exec backend python manage.py migrate
```

Stop only the portal app:

```sh
docker compose stop
```

Check the portal stack:

```sh
docker compose ps
```

Reload nginx after editing `deploy/nginx/portal.local.conf`:

```sh
docker compose exec nginx nginx -s reload
```

The local site is available at:

- `http://127.0.0.1/` through nginx
- `http://127.0.0.1:8080/` through nginx

Both addresses expose the complete portal gateway, including `/api/`,
`/super_admin/`, Django static files, and the Next.js frontend.
