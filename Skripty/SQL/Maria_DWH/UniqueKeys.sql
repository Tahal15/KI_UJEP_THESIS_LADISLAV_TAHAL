ALTER TABLE DimCity
  ADD UNIQUE KEY UK_CityName (CityName);

ALTER TABLE DimSensor
  ADD UNIQUE KEY UK_SensorCode (SensorCode);

ALTER TABLE DimLP
  ADD UNIQUE KEY UK_LicensePlate (LicensePlate);

ALTER TABLE DimDetectionType
  ADD UNIQUE KEY UK_DetectionType (DetectionType);

ALTER TABLE DimVehicleClass
  ADD UNIQUE KEY UK_VehicleClass (VehicleClass);

ALTER TABLE DimCountry
  ADD UNIQUE KEY UK_CountryCode (CountryCode);
