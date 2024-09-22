// Add the Facebook SDK for JavaScript
(function (d, s, id) {
  var js,
    fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) {
    return;
  }
  js = d.createElement(s);
  js.id = id;
  js.src = "https://connect.facebook.net/en_US/sdk.js";
  fjs.parentNode.insertBefore(js, fjs);
})(document, "script", "facebook-jssdk");

window.fbAsyncInit = function () {
  // Initialize the SDK
  FB.init({
    appId: "485822284123595", // Your app ID
    xfbml: true,
    version: "v20.0", // Graph API version
  });

  // Trigger Facebook login on button click
  document.getElementById("fbLoginBtn").addEventListener("click", function () {
    FB.login(
      function (response) {
        console.log(response);
        if (response.authResponse) {
          // Send the authorization code to your server
          fetch("/handle_fb_code", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              code: response.authResponse.code,
            }),
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                document.getElementById("profile").innerHTML =
                  "Käyttöönotto aloitettu onnistuneesti.";
                document.getElementById("fbLoginBtn").style.display = "none";
              } else {
                document.getElementById("profile").innerHTML =
                  "Error: " + data.error;
              }
            });
        } else {
          document.getElementById("profile").innerHTML =
            "Kirjautuminen keskeytetty tai ei viimeistelty.";
        }
      },
      {
        config_id: "1293007491679443", // Your configuration ID
        response_type: "code", // Required for System User Access Token
        override_default_response_type: true,
      }
    );
  });
};
