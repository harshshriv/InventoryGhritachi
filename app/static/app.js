const $ = (id) => document.getElementById(id);
const money = (n) => "$" + Number(n).toFixed(2);

const state = { search: "", category: "", lowOnly: false };

async function api(path, options) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || "Request failed");
  return body;
}

async function loadStats() {
  const s = await api("/api/stats");
  $("stat-items").textContent = s.total_items;
  $("stat-units").textContent = s.total_units;
  $("stat-value").textContent = money(s.total_value);
  $("stat-low").textContent = s.low_stock_count;
}

async function loadItems() {
  const params = new URLSearchParams();
  if (state.search) params.set("search", state.search);
  if (state.category) params.set("category", state.category);
  if (state.lowOnly) params.set("low_stock", "true");
  const items = await api("/api/items?" + params.toString());

  const body = $("items-body");
  body.innerHTML = "";
  $("empty").hidden = items.length > 0;

  for (const it of items) {
    const tr = document.createElement("tr");
    if (it.low_stock) tr.className = "low";
    tr.innerHTML = `
      <td>${escapeHtml(it.name)}${it.low_stock ? '<span class="badge">low</span>' : ""}</td>
      <td>${escapeHtml(it.sku)}</td>
      <td>${escapeHtml(it.category || "—")}</td>
      <td class="num">${it.quantity}</td>
      <td class="num">${it.reorder_level}</td>
      <td class="num">${money(it.unit_price)}</td>
      <td class="num">${money(it.quantity * it.unit_price)}</td>
      <td class="num">
        <button class="link" data-edit="${it.id}">Edit</button>
        <button class="link danger" data-del="${it.id}">Delete</button>
      </td>`;
    body.appendChild(tr);
  }
  window.__items = items;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function refresh() {
  await Promise.all([loadStats(), loadItems()]);
}

// ---- Modal ----
function openModal(item) {
  $("form-error").hidden = true;
  $("form-title").textContent = item ? "Edit item" : "New item";
  $("item-id").value = item ? item.id : "";
  $("f-name").value = item ? item.name : "";
  $("f-sku").value = item ? item.sku : "";
  $("f-category").value = item ? item.category : "";
  $("f-description").value = item ? item.description : "";
  $("f-quantity").value = item ? item.quantity : 0;
  $("f-reorder").value = item ? item.reorder_level : 0;
  $("f-price").value = item ? item.unit_price : 0;
  $("modal").hidden = false;
  $("f-name").focus();
}
function closeModal() { $("modal").hidden = true; }

async function submitForm(e) {
  e.preventDefault();
  const id = $("item-id").value;
  const payload = {
    name: $("f-name").value.trim(),
    sku: $("f-sku").value.trim(),
    category: $("f-category").value.trim(),
    description: $("f-description").value.trim(),
    quantity: Number($("f-quantity").value),
    reorder_level: Number($("f-reorder").value),
    unit_price: Number($("f-price").value),
  };
  try {
    if (id) {
      await api(`/api/items/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    } else {
      await api("/api/items", { method: "POST", body: JSON.stringify(payload) });
    }
    closeModal();
    await refresh();
  } catch (err) {
    const el = $("form-error");
    el.textContent = err.message;
    el.hidden = false;
  }
}

// ---- Events ----
$("search").addEventListener("input", (e) => { state.search = e.target.value; loadItems(); });
$("filter-category").addEventListener("input", (e) => { state.category = e.target.value; loadItems(); });
$("filter-low").addEventListener("change", (e) => { state.lowOnly = e.target.checked; loadItems(); });
$("btn-new").addEventListener("click", () => openModal(null));
$("btn-cancel").addEventListener("click", closeModal);
$("item-form").addEventListener("submit", submitForm);
$("modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });

$("items-body").addEventListener("click", async (e) => {
  const editId = e.target.dataset.edit;
  const delId = e.target.dataset.del;
  if (editId) {
    const item = (window.__items || []).find((i) => i.id == editId);
    openModal(item);
  } else if (delId) {
    if (confirm("Delete this item?")) {
      await api(`/api/items/${delId}`, { method: "DELETE" });
      await refresh();
    }
  }
});

refresh();
