"use client"

import * as React from "react"

import { Button } from "@/components/ui/button"
import StatusCard from "@/components/ui/status-card"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  React.useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex min-h-[70vh] items-center justify-center p-6">
      <div className="w-full max-w-xl space-y-4">
        <StatusCard
          tone="error"
          title="Something went wrong"
          description={
            error?.message ||
            "We hit an unexpected issue while loading this page. Try again or return to the dashboard."
          }
          action={
            <div className="flex flex-wrap gap-2">
              <Button variant="destructive" onClick={reset}>
                Try again
              </Button>
              <Button variant="outline" onClick={() => (window.location.href = "/")}>
                Go to home
              </Button>
            </div>
          }
        />
        {error?.digest ? (
          <p className="text-muted-foreground text-xs">Error reference: {error.digest}</p>
        ) : null}
      </div>
    </div>
  )
}






// [Unit]
// Description=foodnow.site.gunicorn socket

// [Socket]
// ListenStream=/run/foodnow.site.gunicorn.sock

// [Install]
// WantedBy=sockets.target



// nano /etc/systemd/system/foodnow.site.gunicorn.service


// [Unit]
// Description=foodnow.site.gunicorn daemon
// Requires=foodnow.site.gunicorn.socket
// After=network.target

// [Service]
// User=noor
// Group=sudo
// WorkingDirectory=/home/noor/food_now-main/backend
// ExecStart=/home/noor/food_now-main/backend/env/bin/gunicorn \
//           --access-logfile - \
//           --workers 3 \
//           --bind unix:/run/foodnow.site.gunicorn.sock \
//           core.wsgi:application

// [Install]
// WantedBy=multi-user.target

// systemctl start foodnow.site.gunicorn.socket
// systemctl start foodnow.site.gunicorn.service

// systemctl enable foodnow.site.gunicorn.socket
// systemctl enable foodnow.site.gunicorn.service

// systemctl status foodnow.site.gunicorn.socket
// systemctl status foodnow.site.gunicorn.service


// systemctl restart foodnow.site.gunicorn


// nano /etc/nginx/sites-available/foodnow.site

// server {
//     listen 80;
//     listen [::]:80;
//     server_name foodnow.site www.foodnow.site;

//     location /api/ {
//         proxy_pass http://unix:/home/noor/food_now-main/backend/gunicorn.sock;
//     }

//     location / {
//         proxy_pass http://localhost:3000;
//     }

//     location  /static/ {
//         root /var/www/soul;
//     }

//     location  /media/ {
//         root /var/www/soul;
//     }
// }

// sudo certbot --nginx -d foodnow.site -d www.foodnow.site


// server{
//     listen 80;
//     listen [::]:80;

//     server_name foodnow.site www.foodnow.site;

//     location = /favicon.ico { access_log off; log_not_found off; }

//     location /api/ {
//         proxy_set_header Host $http_host;
//         proxy_set_header X-Real-IP $remote_addr;
//         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
//         proxy_set_header X-Forwarded-Proto $scheme;
//         proxy_pass http://unix:/run/foodnow.site.gunicorn.sock;
//     }

//     location / {
//         proxy_pass http://localhost:3000;
//     }


//     location  /static/ {
//         root /var/www/soul;
//     }

//     location  /media/ {
//         root /var/www/soul;
//     }
// }

// ln -s /etc/nginx/sites-available/foodnow.site /etc/nginx/sites-enabled/foodnow.site