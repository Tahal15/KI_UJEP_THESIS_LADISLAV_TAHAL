cube(`DimVehicleClass`, {
  sql: `SELECT * FROM dimvehicleclass`,

  dimensions: {
    VehicleClassKey: { sql: `VehicleClassKey`, primaryKey: true, type: `number` },
    VehicleClass:    { sql: `VehicleClass`,    type: `string` },
  }
});
