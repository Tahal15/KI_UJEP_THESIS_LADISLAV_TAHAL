-- Primární index pro dávkování
CREATE NONCLUSTERED INDEX IX_CameraCamea_LandingID
ON Stg.CameraCamea (LandingID);

-- Pro rychlý lookup v JOINech
CREATE NONCLUSTERED INDEX IX_CameraCamea_OriginalTime
ON Stg.CameraCamea (OriginalTime);

CREATE NONCLUSTERED INDEX IX_CameraCamea_Sensor
ON Stg.CameraCamea (Sensor);

CREATE NONCLUSTERED INDEX IX_CameraCamea_LP
ON Stg.CameraCamea (LP);

CREATE NONCLUSTERED INDEX IX_CameraCamea_DetectionType
ON Stg.CameraCamea (DetectionType);

CREATE NONCLUSTERED INDEX IX_CameraCamea_ILPC
ON Stg.CameraCamea (ILPC);

CREATE NONCLUSTERED INDEX IX_CameraCamea_VehClass
ON Stg.CameraCamea (VehClass);

CREATE NONCLUSTERED INDEX IX_CameraCamea_City
ON Stg.CameraCamea (City);
