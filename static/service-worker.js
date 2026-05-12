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