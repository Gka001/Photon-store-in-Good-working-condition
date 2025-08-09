// cart.js

// Update cart item count in navbar
function updateCartCount() {
  fetch("/cart/count/")
    .then(res => res.json())
    .then(data => {
      const countElem = document.getElementById('cart-count');
      if (countElem) {
        countElem.textContent = data.cart_count;
      }
    });
}

// Update mini cart preview dropdown
function updateMiniCart() {
  fetch("/cart/mini/")
    .then(res => res.json())
    .then(data => {
      const miniCart = document.getElementById("mini-cart-container");
      if (miniCart) {
        miniCart.innerHTML = data.html;
        miniCart.style.display = "block";
        setTimeout(() => miniCart.style.display = "none", 3000);
      }
    });
}

// Handle add-to-cart form submission with AJAX
function setupAddToCartForms() {
  const forms = document.querySelectorAll(".add-to-cart-form");

  forms.forEach(form => {
    form.addEventListener("submit", function(e) {
      e.preventDefault();

      fetch(this.action, {
        method: "POST",
        headers: {
          "X-CSRFToken": this.querySelector("[name=csrfmiddlewaretoken]").value,
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body: new URLSearchParams(new FormData(this))
      })
      .then(res => res.json())
      .then(data => {
        updateCartCount();
        updateMiniCart();

        Swal.fire({
          toast: true,
          icon: 'success',
          title: 'Added to cart',
          position: 'top-end',
          showConfirmButton: false,
          timer: 1500,
          timerProgressBar: true
        });
      })
      .catch(err => {
        Swal.fire({
          icon: 'error',
          title: 'Oops...',
          text: 'Failed to add to cart.'
        });
      });
    });
  });
}

function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const trimmed = cookie.trim();
    if (trimmed.startsWith(name + '=')) {
      return decodeURIComponent(trimmed.substring(name.length + 1));
    }
  }
  return '';
}

function setupCartQuantityButtons() {
  // Increase quantity
  document.querySelectorAll('.cart-increase-btn').forEach(button => {
    button.addEventListener('click', function () {
      const productId = this.dataset.productId;

      fetch(`/cart/increase/${productId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
      })
      .then(response => response.json())
      .then(data => {
        if (data.quantity !== undefined) {
          document.getElementById(`quantity-${productId}`).textContent = data.quantity;
          document.getElementById(`price-${productId}`).textContent = `₹${data.item_total.toFixed(2)}`;
          document.getElementById('cart-total').textContent = `₹${data.cart_total.toFixed(2)}`;
          updateCartCount();
          updateMiniCart();
        }
      });
    });
  });

  // Decrease quantity
  document.querySelectorAll('.cart-decrease-btn').forEach(button => {
    button.addEventListener('click', function () {
      const productId = this.dataset.productId;

      fetch(`/cart/decrease/${productId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
      })
      .then(response => response.json())
      .then(data => {
        if (data.quantity !== undefined) {
          if (data.quantity > 0) {
            document.getElementById(`quantity-${productId}`).textContent = data.quantity;
            document.getElementById(`price-${productId}`).textContent = `₹${data.item_total.toFixed(2)}`;
          } else {
            // Item removed from cart, remove row from table
            const row = document.querySelector(`[data-product-row-id="${productId}"]`);
            if (row) row.remove();
          }
          document.getElementById('cart-total').textContent = `₹${data.cart_total.toFixed(2)}`;
          updateCartCount();
          updateMiniCart();
        }
      });
    });
  });
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  updateCartCount();
  updateMiniCart();
  setupAddToCartForms();
  setupCartQuantityButtons();
});
