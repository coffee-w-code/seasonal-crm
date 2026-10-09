import {
    getInventory,
    getMovementHistory,
} from "../../inventory/services/inventoryApi";

export async function getDashboardData() {
    const [inventoryData, movementData] = await Promise.all([
        getInventory(),
        getMovementHistory(),
    ]);

    return {
        inventory: inventoryData.inventory || [],
        business: inventoryData.business || null,
        movements: movementData.movements || [],
    };
}