cube(`CameraDetections`, {
  sql: `SELECT * FROM FactCameraDetection`,

  joins: {
    DimCity:          { relationship: `belongsTo`, sql: `${CUBE}.CityKey = ${DimCity}.CityKey` },
    DimCountry:       { relationship: `belongsTo`, sql: `${CUBE}.CountryKey = ${DimCountry}.CountryKey` },
    DimDetectionType: { relationship: `belongsTo`, sql: `${CUBE}.DetectionTypeKey = ${DimDetectionType}.DetectionTypeKey` },
    DimLP:            { relationship: `belongsTo`, sql: `${CUBE}.LPKey = ${DimLP}.LPKey` },
    DimSensor:        { relationship: `belongsTo`, sql: `${CUBE}.SensorKey = ${DimSensor}.SensorKey` },
    DimTime:          { relationship: `belongsTo`, sql: `${CUBE}.TimeKey = ${DimTime}.TimeKey` },
    DimVehicleClass:  { relationship: `belongsTo`, sql: `${CUBE}.VehicleClassKey = ${DimVehicleClass}.VehicleClassKey` }
  },

  measures: {
    detectionCount: {
      sql: `CameraDetectionKey`,
      type: `count`,
      title: `Počet detekcí`
    },

    avgVelocity: {
      sql: `CASE WHEN ${CUBE}.Velocity >= 0 THEN ${CUBE}.Velocity ELSE NULL END`,
      type: `avg`,
      title: `Průměrná rychlost (km/h)`
    },

    sumVelocity: {
      sql: `CASE WHEN ${CUBE}.Velocity >= 0 THEN ${CUBE}.Velocity ELSE 0 END`,
      type: `sum`,
      title: `Součet rychlostí`
    },

    minVelocity: {
      sql: `${CUBE}.Velocity`,
      type: `min`,
      title: `Minimální rychlost`
    },

    maxVelocity: {
      sql: `CASE WHEN ${CUBE}.Velocity >= 0 THEN ${CUBE}.Velocity ELSE NULL END`,
      type: `max`,
      title: `Maximální rychlost (km/h)`
    },

    distinctLicensePlates: {
      sql: `${DimLP.LicensePlate}`,
      type: `countDistinct`,
      title: `Počet unikátních SPZ`
    }
  },

  dimensions: {
    CameraDetectionKey: {
      sql: `CameraDetectionKey`,
      type: `number`,
      primaryKey: true,
      title: `Klíč detekce`
    },

    velocity: {
      sql: `Velocity`,
      type: `number`,
      title: `Rychlost (km/h)`
    },

    fullDate: {
      sql: `${DimTime.fullDate}`,
      type: `time`,
      title: `Datum a čas`
    },

    cityName:      { sql: `${DimCity.CityName}`, type: `string`, title: `Město` },
    countryCode:   { sql: `${DimCountry.CountryCode}`, type: `string`, title: `Země` },
    detectionType: { sql: `${DimDetectionType.DetectionType}`, type: `string`, title: `Typ detekce` },
    licensePlate:  { sql: `${DimLP.LicensePlate}`, type: `string`, title: `SPZ` },
    sensorCode:    { sql: `${DimSensor.SensorCode}`, type: `string`, title: `Senzor` },
    vehicleClass:  { sql: `${DimVehicleClass.VehicleClass}`, type: `string`, title: `Třída vozidla` }
  }
});
