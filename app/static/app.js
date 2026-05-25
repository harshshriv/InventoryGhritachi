const $ = (id) => document.getElementById(id);
const money = (n) => "AED " + Number(n || 0).toFixed(2);

const state = { search: "", category: "", status: "", overOnly: false };

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
  $("stat-instock").textContent = s.in_stock_count;
  $("stat-units").textContent = s.units_in_stock;
  $("stat-cost").textContent = money(s.stock_cost_value);
  $("stat-retail").textContent = money(s.stock_retail_value);
  $("stat-sold").textContent = s.sold_count;
  $("stat-revenue").textContent = money(s.sold_revenue);
  $("stat-over").textContent = s.overstocked_count;
}

async function loadItems() {
  const params = new URLSearchParams();
  if (state.search) params.set("search", state.search);
  if (state.category) params.set("category", state.category);
  if (state.status) params.set("status", state.status);
  if (state.overOnly) params.set("overstocked", "true");
  const items = await api("/api/items?" + params.toString());

  const body = $("items-body");
  body.innerHTML = "";
  $("empty").hidden = items.length > 0;

  for (const it of items) {
    const tr = document.createElement("tr");
    const classes = [];
    if (it.status === "Sold") classes.push("sold");
    if (it.overstocked) classes.push("over");
    tr.className = classes.join(" ");
    tr.innerHTML = `
      <td class="num">${it.item_number}</td>
      <td>${escapeHtml(it.category || "—")}</td>
      <td>${escapeHtml(it.name)}</td>
      <td>${escapeHtml(it.size || "—")}</td>
      <td class="num">${it.current_stock}</td>
      <td class="num">${it.on_order}</td>
      <td class="num">${it.max_capacity}${it.overstocked ? '<span class="badge">over</span>' : ""}</td>
      <td class="num">${money(it.price_per_unit)}</td>
      <td class="num">${money(it.cost_per_unit)}</td>
      <td class="num">${it.price_to_cost_ratio ?? "—"}</td>
      <td class="num">${it.sold_price != null ? money(it.sold_price) : "—"}</td>
      <td><span class="pill ${it.status === "Sold" ? "pill-sold" : "pill-stock"}">${it.status}</span></td>
      <td class="num">${money(it.total_value_in_stock)}</td>
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
async function openModal(item) {
  $("form-error").hidden = true;
  $("form-title").textContent = item ? "Edit item" : "New item";
  $("item-id").value = item ? item.id : "";
  if (!item) {
    const meta = await api("/api/meta");
    $("f-number").value = meta.next_item_number;
  } else {
    $("f-number").value = item.item_number;
  }
  $("f-category").value = item ? item.category : "";
  $("f-size").value = item ? item.size : "Free";
  $("f-name").value = item ? item.name : "";
  $("f-description").value = item ? item.description : "";
  $("f-stock").value = item ? item.current_stock : 1;
  $("f-onorder").value = item ? item.on_order : 0;
  $("f-max").value = item ? item.max_capacity : 1;
  $("f-price").value = item ? item.price_per_unit : 0;
  $("f-cost").value = item ? item.cost_per_unit : 0;
  $("f-sold").value = item && item.sold_price != null ? item.sold_price : "";
  $("f-status").value = item ? item.status : "In Stock";
  $("modal").hidden = false;
  $("f-name").focus();
}
function closeModal() { $("modal").hidden = true; }

function numOrNull(id) {
  const v = $(id).value.trim();
  return v === "" ? null : Number(v);
}

async function submitForm(e) {
  e.preventDefault();
  const id = $("item-id").value;
  const payload = {
    item_number: Number($("f-number").value),
    category: $("f-category").value.trim(),
    name: $("f-name").value.trim(),
    size: $("f-size").value.trim() || "Free",
    description: $("f-description").value.trim(),
    current_stock: Number($("f-stock").value),
    on_order: Number($("f-onorder").value),
    max_capacity: Number($("f-max").value),
    price_per_unit: Number($("f-price").value),
    cost_per_unit: Number($("f-cost").value),
    sold_price: numOrNull("f-sold"),
    status: $("f-status").value,
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
$("filter-status").addEventListener("change", (e) => { state.status = e.target.value; loadItems(); });
$("filter-over").addEventListener("change", (e) => { state.overOnly = e.target.checked; loadItems(); });
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
