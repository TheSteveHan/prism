// Get Stripe publishable key
const api = {};
fetch("/api/billing/stripe/config/")
  .then((result) => result.json())
  .then((data) => {
    // Initialize Stripe.js
    api.stripe = Stripe(data.publicKey);
  });

function startCheckout(priceId, successOnRefresh=false) {
  if (!priceId) {
    return;
  }
  // Get Checkout Session ID
  fetch("/api/billing/stripe/checkout/" + priceId + "/")
    .then((result) => {
      return result.json();
    })
    .then((data) => {
      console.log(data);
      if (data.sessionId) {
        // Redirect to Stripe Checkout
        return api.stripe.redirectToCheckout({ sessionId: data.sessionId });
      } else if (data.refresh) {
        if(!successOnRefresh){
          location.reload();
        } else {
          location.href="/welcome"
        }
      }
    })
    .then((res) => {
      console.log(res);
    });
}
