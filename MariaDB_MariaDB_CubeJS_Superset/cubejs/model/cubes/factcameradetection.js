cube(`FactCameraDetection`, {
  sql: `
  SELECT
    CameraDetectionKey,
    Velocity,
    TimeKey,
    SensorKey,
    DetectionTypeKey,
    LPKey,
    CountryKey,
    VehicleClassKey,
    CityKey
  FROM factcameradetection
`,

  joins: {
    DimTime:          { relationship: `belongsTo`, sql: `${FactCameraDetection}.TimeKey         = ${DimTime}.TimeKey` },
    DimSensor:        { relationship: `belongsTo`, sql: `${FactCameraDetection}.SensorKey       = ${DimSensor}.SensorKey` },
    DimDetectionType: { relationship: `belongsTo`, sql: `${FactCameraDetection}.DetectionTypeKey= ${DimDetectionType}.DetectionTypeKey` },
    DimLP:            { relationship: `belongsTo`, sql: `${FactCameraDetection}.LPKey           = ${DimLP}.LPKey` },
    DimCountry:       { relationship: `belongsTo`, sql: `${FactCameraDetection}.CountryKey      = ${DimCountry}.CountryKey` },
    DimVehicleClass:  { relationship: `belongsTo`, sql: `${FactCameraDetection}.VehicleClassKey = ${DimVehicleClass}.VehicleClassKey` },
    DimCity:          { relationship: `belongsTo`, sql: `${FactCameraDetection}.CityKey         = ${DimCity}.CityKey` },
  },

  measures: {
    detectionCount: { type: `count`, drillMembers: [id, fullDate] },

    avgVelocity: {
      sql: `CASE WHEN ${CUBE}.Velocity > 0 THEN ${CUBE}.Velocity ELSE NULL END`,
      type: `avg`,
      title: `Průměrná rychlost (> 0 km/h)`
    },
    minVelocity: { sql: `Velocity`, type: `min`, title: `Min. rychlost (km/h)` },
   maxVelocity: {  sql: `Velocity`, type: `max`, title: `Max. rychlost (km/h)`},

    uniquePlates: {
      sql: `${DimLP.LicensePlate}`,
      type: `countDistinct`,
      title: `Počet unikátních SPZ`
    },

    detectionCountWithVelocity: {
      sql: `CASE WHEN ${CUBE}.Velocity > 0 THEN 1 ELSE NULL END`,
      type: `count`,
      title: `Počet detekcí s rychlostí > 0`
    }
  },

  dimensions: {
    timeKey:         { sql: `TimeKey`, type: `number`, public: false },
    sensorKey:       { sql: `SensorKey`, type: `number`, public: false },
    detectionTypeKey:{ sql: `DetectionTypeKey`, type: `number`, public: false },
    lpKey:           { sql: `LPKey`, type: `number`, public: false },
    countryKey:      { sql: `CountryKey`, type: `number`, public: false },
    vehicleClassKey: { sql: `VehicleClassKey`, type: `number`, public: false },
    cityKey:         { sql: `CityKey`, type: `number`, public: false },

    cityName:        { sql: `${DimCity.CityName}`, type: `string`, title: `Město` },
    countryCode:     { sql: `${DimCountry.CountryCode}`, type: `string`, title: `Země` },
    detectionType:   { sql: `${DimDetectionType.DetectionType}`, type: `string`, title: `Typ detekce` },
    sensorCode:      { sql: `${DimSensor.SensorCode}`, type: `string`, title: `Senzor` },
    vehicleClass:    { sql: `${DimVehicleClass.VehicleClass}`, type: `string`, title: `Třída vozidla` },
    licensePlate:    { sql: `${DimLP.LicensePlate}`, type: `string`, title: `SPZ` },
    fullDate:        { sql: `${DimTime.fullDate}`, type: `time` },
    
    id:              { sql: `CameraDetectionKey`, type: `number`, primaryKey: true },

    monthYearMerged: {
      sql: `
        CONCAT(
          ${DimTime.year},
          '-',
          LPAD(${DimTime.month}, 2, '0'),
          ' ',
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
        )
      `,
      type: 'string',
      title: 'Měsíc a rok (řaditelný)'
    }
  }
});
