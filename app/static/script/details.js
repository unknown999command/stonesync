function executeScripts(html) {
  var tempDiv = document.createElement("div");
  tempDiv.innerHTML = html;
  var scripts = tempDiv.querySelectorAll("script");
  scripts.forEach((script) => {
    var newScript = document.createElement("script");
    newScript.text = script.textContent;
    document.head.appendChild(newScript).parentNode.removeChild(newScript);
  });
}

document.querySelectorAll(".order").forEach((order) => {
  order.addEventListener("click", function () {
    document.getElementById("loading-overlay").style.display = "flex";
    let orderId = this.getAttribute("data-order-id");
    try {
      document.getElementById("new" + orderId).style.display = "None";
    } catch (error) {}
    let detailsRow = this.nextElementSibling;
    if (detailsRow && detailsRow.classList.contains("order-details-loaded")) {
      detailsRow.style.display =
        detailsRow.style.display === "none" || detailsRow.style.display === ""
          ? "table-row"
          : "none";
      document.getElementById("loading-overlay").style.display = "none";
      return;
    }
    fetch(`/order_details/${orderId}`)
      .then((response) => response.text())
      .then((data) => {
        if (
          !detailsRow ||
          !detailsRow.classList.contains("order-details-loaded")
        ) {
          detailsRow = document.createElement("tr");
          detailsRow.classList.add("order-details-loaded");
          detailsRow.id = `tr-order-${orderId}`;
          detailsRow.innerHTML = `<td colspan="5">${data}</td>`;
          this.parentNode.insertBefore(detailsRow, this.nextSibling);
        }

        executeScripts(data);

        detailsRow.style.display = "table-row";

        document.getElementById("loading-overlay").style.display = "none";
      })
      .catch((error) => console.error("Error fetching order details:", error));
  });
});
