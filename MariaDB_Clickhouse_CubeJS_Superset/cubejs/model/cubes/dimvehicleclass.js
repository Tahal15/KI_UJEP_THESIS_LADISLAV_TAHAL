cube(`DimVehicleClass`, {
  sql: `SELECT * FROM DimVehicleClass`,

  dimensions: {
    VehicleClassKey: {
      sql: `toString(VehicleClassKey)`,
      primaryKey: true,
      type: `string`,
      title: `Klíč třídy vozidla`
    },

    VehicleClass: {
      sql: `VehicleClass`,
      type: `string`,
      title: `Třída vozidla`
    }
  }
});
