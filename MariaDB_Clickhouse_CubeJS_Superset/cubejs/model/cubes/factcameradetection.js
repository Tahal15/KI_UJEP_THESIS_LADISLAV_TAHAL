cube(`FactCameraDetection`, {
  sql: `
    SELECT
      CameraDetectionKey,
      Velocity,
      CAST(DetectionTypeKey AS String) AS DetectionTypeKey,
      TimeKey,
      SensorKey,
      LPKey,
      CountryKey,
      VehicleClassKey,
      CityKey
    FROM FactCameraDetection
  `,

  // ===== JOINS =====
  joins: {
    DimTime: {
      relationship: `belongsTo`,
      sql: `${CUBE}.TimeKey = ${DimTime}.TimeKey`
    },
    DimSensor: {
      relationship: `belongsTo`,
      sql: `${CUBE}.SensorKey = ${DimSensor}.SensorKey`
    },
    DimDetectionType: {
      relationship: `belongsTo`,
      sql: `toString(${CUBE}.DetectionTypeKey) = toString(${DimDetectionType}.DetectionTypeKey)`
    },
    DimLP: {
      relationship: `belongsTo`,
      sql: `${CUBE}.LPKey = ${DimLP}.LPKey`
    },
    DimCountry: {
      relationship: `belongsTo`,
      sql: `${CUBE}.CountryKey = ${DimCountry}.CountryKey`
    },
    DimVehicleClass: {
      relationship: `belongsTo`,
      sql: `${CUBE}.VehicleClassKey = ${DimVehicleClass}.VehicleClassKey`
    },
    DimCity: {
      relationship: `belongsTo`,
      sql: `${CUBE}.CityKey = ${DimCity}.CityKey`
    },
  },

  // ===== MEASURES =====
  measures: {
    // Počet všech detekcí
    detections: {
      type: `count`,
      title: `Počet detekcí`
    },

    // Unikátní typy detekce
    detectionTypeDistinct: {
      sql: `DetectionTypeKey`,
      type: `countDistinct`,
      title: `Počet unikátních typů detekce`
    },

    // Počet detekcí s rychlostí > 0
    detectionsWithVelocity: {
      sql: `CASE WHEN ${CUBE}.Velocity > 0 THEN 1 ELSE NULL END`,
      type: `sum`,
      title: `Počet detekcí s rychlostí > 0`
    },

    // Rychlosti
    avgVelocity: {
      sql: `CASE WHEN ${CUBE}.Velocity > 0 THEN ${CUBE}.Velocity ELSE NULL END`,
      type: `avg`,
      title: `Průměrná rychlost (> 0 km/h)`
    },
    minVelocity: { sql: `Velocity`, type: `min`, title: `Min. rychlost (km/h)` },
    maxVelocity: { sql: `Velocity`, type: `max`, title: `Max. rychlost (km/h)` },

    // Unikátní SPZ
    uniquePlates: {
      sql: `${DimLP.LicensePlate}`,
      type: `countDistinct`,
      title: `Počet unikátních SPZ`
    }
  },

  // ===== DIMENSIONS =====
  dimensions: {
    id: { sql: `CameraDetectionKey`, primaryKey: true, type: `number` },

    // Klíče
    timeKey:         { sql: `TimeKey`, type: `number`, public: false },
    sensorKey:       { sql: `SensorKey`, type: `number`, public: false },
    detectionTypeKey:{ sql: `DetectionTypeKey`, type: `number`, title: `Klíč typu detekce` },
    lpKey:           { sql: `LPKey`, type: `number`, public: false },
    countryKey:      { sql: `CountryKey`, type: `number`, public: false },
    vehicleClassKey: { sql: `toString(VehicleClassKey)`, type: `string`, public: false },
    cityKey:         { sql: `CityKey`, type: `number`, public: false },

    // Popisné dimenze
    cityName:      { sql: `${DimCity.CityName}`, type: `string`, title: `Město` },
    countryCode:   { sql: `${DimCountry.CountryCode}`, type: `string`, title: `Země` },
    sensorCode:    { sql: `${DimSensor.SensorCode}`, type: `string`, title: `Senzor` },
    vehicleClass:  { sql: `${DimVehicleClass.VehicleClass}`, type: `string`, title: `Třída vozidla` },
    licensePlate:  { sql: `${DimLP.LicensePlate}`, type: `string`, title: `SPZ` },
    detectionType:  { sql: `${DimDetectionType.DetectionType}`, type: `string`, title: `Detekce`},
    

    // Časové dimenze
    fullDate: { sql: `${DimTime.fullDate}`, type: `time`, title: `Datum a čas` },
    year: { sql: `${DimTime.year}`, type: `number`, title: `Rok` },
    monthNumber: { sql: `${DimTime.month}`, type: `number`, title: `Měsíc (číslo)` },
    day: { sql: `${DimTime.day}`, type: `number`, title: `Den v měsíci` },

    // Český název měsíce
    monthName: {
      sql: `
        CASE ${DimTime.month}
          WHEN 1 THEN 'Leden'
          WHEN 2 THEN 'Únor'
          WHEN 3 THEN 'Březen'
          WHEN 4 THEN 'Duben'
          WHEN 5 THEN 'Květen'
          WHEN 6 THEN 'Červen'
          WHEN 7 THEN 'Červenec'
          WHEN 8 THEN 'Srpen'
          WHEN 9 THEN 'Září'
          WHEN 10 THEN 'Říjen'
          WHEN 11 THEN 'Listopad'
          WHEN 12 THEN 'Prosinec'
        END
      `,
      type: 'string',
      title: 'Měsíc (název)'
    },

    yearMonthSort: {
      sql: `${DimTime.year} * 100 + ${DimTime.month}`,
      type: `number`,
      title: `Rok-Měsíc (řaditelný)`
    },

    monthYearMerged: {
      sql: `
        CONCAT(
          ${DimTime.year}, '-',
          LPAD(${DimTime.month}::text, 2, '0'), ' ',
          CASE ${DimTime.month}
            WHEN 1 THEN 'Leden' WHEN 2 THEN 'Únor' WHEN 3 THEN 'Březen' WHEN 4 THEN 'Duben'
            WHEN 5 THEN 'Květen' WHEN 6 THEN 'Červen' WHEN 7 THEN 'Červenec' WHEN 8 THEN 'Srpen'
            WHEN 9 THEN 'Září' WHEN 10 THEN 'Říjen' WHEN 11 THEN 'Listopad' WHEN 12 THEN 'Prosinec'
          END
        )
      `,
      type: 'string',
      title: 'Měsíc a rok (řaditelný popisek)'
    }
  }
});
