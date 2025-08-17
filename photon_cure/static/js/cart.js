// cart.js

function updateCartCount() {
  fetch("/cart/count/")
    .then(res => res.json())
    .then(data => {
      const el = document.getElementById('cart-count');
      if (el) el.textContent = data.cart_count;
    });
}

function updateMiniCart() {
  fetch("/cart/mini/")
    .then(res => res.json())
    .then(data => {
      const mc = document.getElementById("mini-cart-container");
      if (!mc) return;
      mc.innerHTML = data.html;
      mc.style.display = "block";
      setTimeout(() => mc.style.display = "none", 3000);
    });
}

// Optional toast helper, safe if Swal missing
function toastInfo(msg) {
  if (window.Swal) {
    Swal.fire({toast:true,icon:'info',title:msg,position:'top-end',showConfirmButton:false,timer:1200});
  }
}

function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let c of cookies) {
    const t = c.trim();
    if (t.startsWith(name + '=')) return decodeURIComponent(t.substring(name.length + 1));
  }
  return '';
}

function togglePlusUI(productId, currentQty, maxQty) {
  const row = document.querySelector(`tr[data-product-row-id="${productId}"]`);
  if (!row) return;
  const plusBtn = row.querySelector('.cart-increase-btn');
  const atMax = currentQty >= maxQty && currentQty > 0;

  if (plusBtn) {
    plusBtn.disabled = atMax;
    plusBtn.title = atMax ? 'Max stock reached' : '';
    plusBtn.classList.toggle('btn-outline-secondary', !atMax);
    plusBtn.classList.toggle('btn-secondary', atMax);
    plusBtn.setAttribute('aria-disabled', atMax ? 'true' : 'false');
  }
  const maxMsg = document.getElementById(`max-msg-${productId}`);
  if (maxMsg) maxMsg.classList.toggle('d-none', !atMax);
}

function handleIncrease(plusBtn) {
  // If disabled, nothing to do
  if (plusBtn.disabled) return;

  const productId = plusBtn.dataset.productId;
  const row = plusBtn.closest('tr');
  const maxAttr = plusBtn.getAttribute('data-max') || row?.getAttribute('data-max') || '999999';
  const maxQty = parseInt(maxAttr, 10);

  fetch(`/cart/increase/${productId}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCSRFToken(), 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
  })
  .then(r => r.json())
  .then(data => {
    if (typeof data.quantity !== 'number') return;

    const qtyEl = document.getElementById(`quantity-${productId}`);
    const priceEl = document.getElementById(`price-${productId}`);
    const cartTotalEl = document.getElementById('cart-total');

    if (qtyEl) qtyEl.textContent = data.quantity;
    if (priceEl) priceEl.textContent = `₹${data.item_total.toFixed(2)}`;
    if (cartTotalEl) cartTotalEl.textContent = `₹${data.cart_total.toFixed(2)}`;

    updateCartCount();
    updateMiniCart();

    if (!isNaN(maxQty)) {
      togglePlusUI(productId, data.quantity, maxQty);
      if (data.quantity >= maxQty) toastInfo(`Only ${maxQty} in stock`);
    }
  });
}

function handleDecrease(minusBtn) {
  const productId = minusBtn.dataset.productId;
  const row = minusBtn.closest('tr');
  const maxAttr = row?.getAttribute('data-max') || '999999';
  const maxQty = parseInt(maxAttr, 10);

  fetch(`/cart/decrease/${productId}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCSRFToken(), 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
  })
  .then(r => r.json())
  .then(data => {
    if (typeof data.quantity !== 'number') return;

    if (data.quantity > 0) {
      const qtyEl = document.getElementById(`quantity-${productId}`);
      const priceEl = document.getElementById(`price-${productId}`);
      if (qtyEl) qtyEl.textContent = data.quantity;
      if (priceEl) priceEl.textContent = `₹${data.item_total.toFixed(2)}`;
    } else {
      // removed
      const tr = row || document.querySelector(`tr[data-product-row-id="${productId}"]`);
      if (tr) tr.remove();
    }

    const cartTotalEl = document.getElementById('cart-total');
    if (cartTotalEl) cartTotalEl.textContent = `₹${data.cart_total.toFixed(2)}`;

    updateCartCount();
    updateMiniCart();

    // Immediately re-enable + and hide "max" message if below ceiling
    if (!isNaN(maxQty) && data.quantity > 0) {
      togglePlusUI(productId, data.quantity, maxQty);
    }
  });
}

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
      .then(() => {
        updateCartCount();
        updateMiniCart();
        if (window.Swal) Swal.fire({ toast:true, icon:'success', title:'Added to cart', position:'top-end', showConfirmButton:false, timer:1500, timerProgressBar:true });
      })
      .catch(() => {
        if (window.Swal) Swal.fire({ icon:'error', title:'Oops...', text:'Failed to add to cart.' });
      });
    });
  });
}

// === Event delegation: robustly handles clicks even if buttons start disabled or change ===
document.addEventListener('click', (e) => {
  const plus = e.target.closest('.cart-increase-btn');
  if (plus) {
    e.preventDefault();
    handleIncrease(plus);
    return;
  }
  const minus = e.target.closest('.cart-decrease-btn');
  if (minus) {
    e.preventDefault();
    handleDecrease(minus);
  }
});

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  updateCartCount();
  updateMiniCart();
  setupAddToCartForms();
});
