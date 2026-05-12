self.addEventListener("install", event => {

    console.log("Service Worker Installed");

});

self.addEventListener("activate", event => {

    console.log("Service Worker Activated");

});

self.addEventListener("push", event => {

    const data = event.data.json();

    self.registration.showNotification(
        data.title,
        {
            body: data.body,

            icon: "/static/images/logo.png",

            badge: "/static/images/logo.png"
        }
    );

});