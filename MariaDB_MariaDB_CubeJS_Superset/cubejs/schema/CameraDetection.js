cube(`CameraDetections`, {
  sql: `SELECT * FROM FactCameraDetection`,

  joins: {
    DimCity: { sql: `${CUBE}.CityKey = ${DimCity}.CityKey`, relationship: `belongsTo` },
    DimCountry: { sql: `${CUBE}.CountryKey = ${DimCountry}.CountryKey`, relationship: `belongsTo` },
    DimDetectionType: { sql: `${CUBE}.DetectionTypeKey = ${DimDetectionType}.DetectionTypeKey`, relationship: `belongsTo` },
    DimLP: { sql: `${CUBE}.LPKey = ${DimLP}.LPKey`, relationship: `belongsTo` },
    DimSensor: { sql: `${CUBE}.SensorKey = ${DimSensor}.SensorKey`, relationship: `belongsTo` },
    DimTime: { sql: `${CUBE}.TimeKey = ${DimTime}.TimeKey`, relationship: `belongsTo` },
    DimVehicleClass: { sql: `${CUBE}.VehicleClassKey = ${DimVehicleClass}.VehicleClassKey`, relationship: `belongsTo` }
  },

  measures: {
    detectionCount: { type: `count`, sql: `CameraDetectionKey`, drillMembers: [CameraDetectionKey] },
    avgVelocity: { sql: `Velocity`, type: `avg` },
    sumVelocity: { sql: `Velocity`, type: `sum` },
    minVelocity: { sql: `Velocity`, type: `min` },
    maxVelocity: { sql: `Velocity`, type: `max` },
    distinctVelocityCount: { sql: `Velocity`, type: `countDistinct` }
  },

  dimensions: {
    CameraDetectionKey: { sql: `CameraDetectionKey`, type: `string`, primaryKey: true },
    detectionDate: { sql: `${DimTime}.Date`, type: `time` },
    cityName: { sql: `${DimCity}.CityName`, type: `string` },
    countryName: { sql: `${DimCountry}.CountryName`, type: `string` },
    detectionType: { sql: `${DimDetectionType}.DetectionType`, type: `string` },
    lpNumber: { sql: `${DimLP}.LicensePlate`, type: `string` },
    sensorCode: { sql: `${DimSensor}.SensorCode`, type: `string` },
    vehicleClassName: { sql: `${DimVehicleClass}.VehicleClassName`, type: `string` }
  }
});
