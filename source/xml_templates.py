training_center_database = u"""<?xml version='1.0' encoding='utf-8'?>
<TrainingCenterDatabase xmlns:ns2="http://www.garmin.com/xmlschemas/UserProfile/v2" xmlns:ns3="http://www.garmin.com/xmlschemas/ActivityExtension/v2" xmlns:ns5="http://www.garmin.com/xmlschemas/ActivityGoals/v1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2" xsi:schemaLocation="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd">
  <Activities>
    <Activity Sport="${header['sport'] | x}">
      <Id>${header['id']}</Id>
      <Lap StartTime="${header['start_time']}">
        <TotalTimeSeconds>${header['total_time']}</TotalTimeSeconds>
        <DistanceMeters>${header['distance_meters']}</DistanceMeters>
        <MaximumSpeed>0</MaximumSpeed>
        <Calories>0</Calories>
        <AverageHeartRateBpm>
          <Value>${header['average_heart_rate']}</Value>
        </AverageHeartRateBpm>
        <MaximumHeartRateBpm>
          <Value>${header['maximum_heart_rate']}</Value>
        </MaximumHeartRateBpm>
        <Intensity>Active</Intensity>
        <Cadence>0</Cadence>
        <TriggerMethod>Manual</TriggerMethod>
        <Track>
          %for point in points:
          <Trackpoint>
            <Time>${point['time']}</Time>
            <HeartRateBpm>
              <Value>${point['bpm']}</Value>
            </HeartRateBpm>
            <Cadence>${point['cadence']}</Cadence>
            <DistanceMeters>${point['distance_meters']}</DistanceMeters>
            <Extensions>
              <TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2">
                <Watts>${point['watts']}</Watts>
              </TPX>
            </Extensions>
          </Trackpoint>
          %endfor
        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>
"""
