cube(`DimTime`, {
  sql: `SELECT * FROM dimtime`,

  dimensions: {
    TimeKey:    { sql: `TimeKey`, primaryKey: true, type: `number` },

    /** Datum + čas – jediná TIME dimenze, po které půjde v Supersetu libovolně „group-by“ */
    fullDate:   { sql: `FullDate`, type: `time` },

    year:       { sql: `YearNum`,      type: `number` },
    month:      { sql: `MonthNum`,     type: `number` },
    day:        { sql: `DayNum`,       type: `number` },
    weekday:    { sql: `DayOfWeekNum`, type: `number` },
    hour:       { sql: `HourNum`,      type: `number` },
    minute:     { sql: `MinuteNum`,    type: `number` },
  }
});
