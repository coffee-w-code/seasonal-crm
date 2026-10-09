import apiClient from "../../../api/client";

export async function getInventory() {
    const response = await apiClient.get("/inventory/stock/");

    return response.data;
}

export async function moveStock({
    productId,
    quantity,
    source,
    destination,
    notes = "",
}) {
    const response = await apiClient.post("/inventory/move/", {
        product_id: productId,
        quantity,
        source,
        destination,
        notes,
    });

    return response.data;
}

export async function getMovementHistory() {
    const response = await apiClient.get("/inventory/movements/");

    return response.data;
}