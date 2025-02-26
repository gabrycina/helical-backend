# 🧬 Helical backend quick start

## Running the Backend

1. Build the Docker image:
```bash
# From the helical-backend directory
cd helical-workflow/helical-backend
docker build -t helical-backend .
```

2. Run the container:
```bash
docker run -p 80:80 helical-backend:latest
```

The API will be available at http://localhost:80

## Frontend Development

Make sure your frontend is configured to talk to the backend:
```env
# in helical-frontend/.env
VITE_API_URL=http://localhost:80/api/v1
```

## API Documentation

Once running, view the API docs at:
http://localhost:80/docs 