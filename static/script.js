// static/script.js
// Central frontend JS for the app — robust and defensive

// small helper
const $ = id => document.getElementById(id);

// Simple section navigation
// Pass the event when calling from an inline onclick: showSection('soil-crop', event)
function showSection(sectionId, ev) {
  const sections = document.querySelectorAll('.section');
  sections.forEach(s => s.classList.remove('active'));
  const targetSection = $(sectionId);
  if (targetSection) targetSection.classList.add('active');

  // update nav active class (works even if nav uses anchors or buttons)
  document.querySelectorAll('nav button, nav a').forEach(b => b.classList.remove('active'));

  // If event provided, prefer using it to locate the clicked nav item
  if (ev && ev.currentTarget) {
    ev.currentTarget.classList.add('active');
    return;
  }

  // Otherwise, try to find a nav button/link with matching text
  const normalized = sectionId.replace(/-/g, ' ').trim().toLowerCase();
  Array.from(document.querySelectorAll('nav button, nav a')).find(b => {
    if (!b.textContent) return false;
    if (b.textContent.trim().toLowerCase().includes(normalized)) {
      b.classList.add('active');
      return true;
    }
    return false;
  });
}
window.showSection = showSection; // expose for inline use

// TALUKA dropdown: fetch talukas for a district
async function updateTalukas() {
  const districtEl = $('district');
  const talukaSelect = $('taluka');
  if (!talukaSelect) return;

  const district = districtEl ? districtEl.value : '';
  talukaSelect.innerHTML = '<option>Loading...</option>';
  if (!district) {
    talukaSelect.innerHTML = '<option value="">First select a district</option>';
    return;
  }

  try {
    const res = await fetch(`/api/talukas/${encodeURIComponent(district)}`);
    if (!res.ok) {
      talukaSelect.innerHTML = '<option value="">Error loading</option>';
      return;
    }
    const talukas = await res.json();
    talukaSelect.innerHTML = '<option value="">Choose taluka</option>';
    if (Array.isArray(talukas) && talukas.length) {
      talukas.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        talukaSelect.appendChild(opt);
      });
    } else {
      talukaSelect.innerHTML = '<option value="">No talukas found</option>';
    }
  } catch (e) {
    console.error('updateTalukas error', e);
    talukaSelect.innerHTML = '<option value="">Error loading</option>';
  }
}
window.updateTalukas = updateTalukas;

// Soil-crop form submit
document.addEventListener('submit', async function (evt) {
  const form = evt.target;
  if (!form) return;

  // only act for soil-crop-form
  if (form.id !== 'soil-crop-form') return;

  evt.preventDefault();
  const district = $('district')?.value;
  const taluka = $('taluka')?.value;
  if (!district || !taluka) {
    alert('Select district & taluka');
    return;
  }

  try {
    const res = await fetch(`/api/soil-crop/${encodeURIComponent(district)}/${encodeURIComponent(taluka)}`);
    if (!res.ok) {
      alert('Data not found for selected location');
      return;
    }
    const data = await res.json();

    $('selected-location') && ( $('selected-location').textContent = district + ' / ' + taluka );
    $('soil-type') && ( $('soil-type').textContent = data.soilType || '-' );
    $('ph-level') && ( $('ph-level').textContent = data.phLevel || '-' );
    $('kharif-crops') && ( $('kharif-crops').textContent = data.kharifCrops || '-' );
    $('rabi-crops') && ( $('rabi-crops').textContent = data.rabiCrops || '-' );
    $('irrigation') && ( $('irrigation').textContent = data.irrigation || '-' );
    $('fertilizer') && ( $('fertilizer').textContent = data.fertilizer || '-' );
    const soilResults = $('soil-results');
    if (soilResults) soilResults.style.display = 'block';

    // show the soil-crop section (use the function, no event)
    showSection('soil-crop');
  } catch (err) {
    console.error('soil-crop fetch error', err);
    alert('Error fetching recommendations');
  }
});

// Weather - load current by location input
async function loadWeather() {
  const loc = $('weather-location')?.value || '';
  if (!loc) return;
  try {
    const res = await fetch(`/api/weather/${encodeURIComponent(loc)}`);
    if (!res.ok) {
      console.warn('weather API returned non-ok');
      return;
    }
    const data = await res.json();
    $('weather-city') && ( $('weather-city').textContent = data.location || loc );
    $('current-temp') && ( $('current-temp').textContent = typeof data.temp !== 'undefined' ? data.temp : '-' );
    $('weather-icon') && ( $('weather-icon').textContent = data.icon || '' );
    $('current-condition') && ( $('current-condition').textContent = data.condition || '' );
    $('humidity') && ( $('humidity').textContent = data.humidity || '-' );
    $('wind-speed') && ( $('wind-speed').textContent = data.windSpeed || '-' );
    $('rainfall') && ( $('rainfall').textContent = data.rainfall || '-' );
  } catch (e) {
    console.error('loadWeather error', e);
  }
}
window.loadWeather = loadWeather;

// 3-day or N-day forecast
async function loadForecast() {
  try {
    const res = await fetch('/api/weather/forecast');
    if (!res.ok) return;
    const days = await res.json();
    const container = $('forecast-container');
    if (!container) return;
    container.innerHTML = '';
    if (!Array.isArray(days) || !days.length) {
      container.innerHTML = '<div class="card">No forecast available</div>';
      return;
    }
    days.forEach(d => {
      const div = document.createElement('div');
      div.className = 'card';
      div.style.textAlign = 'center';
      const day = d.day || '';
      const icon = d.icon || '';
      const temp = typeof d.temp !== 'undefined' ? `${d.temp}°C` : '-';
      div.innerHTML = `<div style="font-weight:700">${escapeHtml(day)}</div><div style="font-size:1.5rem">${escapeHtml(icon)}</div><div style="opacity:0.8">${escapeHtml(temp)}</div>`;
      container.appendChild(div);
    });
  } catch (e) {
    console.error('loadForecast error', e);
  }
}

// Advisory
async function loadAdvisory() {
  try {
    const res = await fetch('/api/advisory');
    if (!res.ok) return;
    const j = await res.json();
    $('agri-advisory') && ( $('agri-advisory').textContent = j.advisory || '' );
  } catch (e) {
    console.error('loadAdvisory error', e);
  }
}

// Marketplace: load products
async function loadProducts(category = 'all', search = '') {
  try {
    // if the products container is not present (we hid the marketplace listing), skip fetching
    const container = $('products-container');
    if (!container) return;

    const url = new URL('/api/products/filter', window.location.origin);
    if (category) url.searchParams.set('category', category);
    if (search) url.searchParams.set('search', search);
    const res = await fetch(url);
    if (!res.ok) return;
    const products = await res.json();
    container.innerHTML = '';
    if (!Array.isArray(products) || !products.length) {
      container.innerHTML = '<div class="card">No products found</div>';
      return;
    }
    products.forEach(p => {
      const card = document.createElement('div');
      card.className = 'card product-card';
      card.innerHTML = `<div class="icon">${escapeHtml(p.icon || '')}</div>
        <div>
          <div style="font-weight:700">${escapeHtml(p.name || '')} - ₹${escapeHtml(String(p.price || '0'))}</div>
          <div style="opacity:0.8;font-size:0.95rem">${escapeHtml(p.quantity || '')} • ${escapeHtml(p.location || '')} • ${escapeHtml(p.seller || '')}</div>
        </div>`;
      container.appendChild(card);
    });
  } catch (e) {
    console.error('loadProducts error', e);
  }
}
window.loadProducts = loadProducts;

function filterCategory(cat) {
  loadProducts(cat, $('marketplace-search')?.value || '');
}
function filterProducts() {
  const s = $('marketplace-search')?.value || '';
  loadProducts('all', s);
}
window.filterCategory = filterCategory;
window.filterProducts = filterProducts;

// Add product form
document.addEventListener('submit', async function (evt) {
  const form = evt.target;
  if (!form || form.id !== 'add-product-form') return;

  evt.preventDefault();
  const data = {
    name: $('product-name')?.value || '',
    category: $('product-category')?.value || '',
    quantity: $('product-quantity')?.value || '',
    price: Number($('product-price')?.value || 0),
    seller: $('seller-name')?.value || '',
    contact: $('seller-contact')?.value || '',
    location: $('seller-location')?.value || ''
  };
  try {
    const res = await fetch('/api/products/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const json = await res.json();
    if (json.success) {
      alert('Listing added');
      // only reload products if the products container exists
      if ($('products-container')) loadProducts();
      form.reset();
    } else {
      alert('Could not add: ' + (json.error || 'Unknown'));
    }
  } catch (e) {
    console.error('add product error', e);
    alert('Error adding product');
  }
});

// Schemes
async function loadSchemes(category = 'all', search = '') {
  try {
    const url = new URL('/api/schemes/filter', window.location.origin);
    if (category) url.searchParams.set('category', category);
    if (search) url.searchParams.set('search', search);
    const res = await fetch(url);
    if (!res.ok) return;
    const schemes = await res.json();
    const container = $('schemes-container');
    if (!container) return;
    container.innerHTML = '';
    if (!Array.isArray(schemes) || !schemes.length) {
      container.innerHTML = '<div class="card">No schemes found</div>';
      return;
    }
    schemes.forEach(s => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `<h3 style="color:var(--primary-green)">${escapeHtml(s.name || '')}</h3>
        <div style="opacity:0.9">${escapeHtml(s.category || '')}</div>
        <p>${escapeHtml(s.description || '')}</p>
        <div style="font-size:0.9rem;color:var(--muted)"><strong>How to apply:</strong> ${escapeHtml(s.howToApply || '-')}</div>`;
      container.appendChild(card);
    });
  } catch (e) {
    console.error('loadSchemes error', e);
  }
}
function filterSchemeCategory(cat) { loadSchemes(cat, $('scheme-search')?.value || ''); }
function filterSchemes() { loadSchemes('all', $('scheme-search')?.value || ''); }
window.loadSchemes = loadSchemes;
window.filterSchemeCategory = filterSchemeCategory;
window.filterSchemes = filterSchemes;

// OTP helper used by insurance form (if used inline)
function sendOTP() {
  // Replace with real OTP flow in production
  alert('OTP sent to your mobile number!\nDemo OTP: 123456');
}
window.sendOTP = sendOTP;

// small utility: escape text for insertion into innerHTML from API data
function escapeHtml(unsafe) {
  if (unsafe == null) return '';
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// initial boot (safe)
document.addEventListener('DOMContentLoaded', function () {
  // call loadProducts only when container exists (the server may hide the block)
  if (document.getElementById('products-container')) {
    loadProducts();
  }
  loadSchemes();
  loadWeather();
  loadForecast();
  loadAdvisory();

  // if there are nav buttons that should call showSection, attach event listeners
  document.querySelectorAll('nav button, nav a').forEach(el => {
    const target = el.getAttribute('data-target') || el.getAttribute('href') || el.textContent;
    // if data-target exists we prefer it; otherwise no automatic behavior
    el.addEventListener('click', function (ev) {
      // try to derive sectionId from data-target or href like '#soil-crop'
      const dt = el.getAttribute('data-target');
      if (dt) {
        showSection(dt, ev);
      } else {
        // if href is an anchor (#...), use that
        const href = el.getAttribute('href') || '';
        if (href && href.startsWith('#')) {
          const id = href.slice(1);
          showSection(id, ev);
          ev.preventDefault();
        }
      }
    });
  });
});