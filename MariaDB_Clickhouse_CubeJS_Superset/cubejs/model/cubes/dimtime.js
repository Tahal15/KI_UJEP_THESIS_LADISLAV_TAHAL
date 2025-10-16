cube(`DimTime`, {
  sql: `SELECT * FROM DimTime`,

  dimensions: {
    TimeKey: {
      sql: `TimeKey`,
      primaryKey: true,
      type: `number`,
      title: `Klíč času`
    },

    fullDate: {
      sql: `FullDate`,
      type: `time`,
      title: `Datum a čas`
    },

    year: {
      sql: `YearNum`,
      type: `number`,
      title: `Rok`
    },

    month: {
      sql: `MonthNum`,
      type: `number`,
      title: `Měsíc`
    },

    day: {
      sql: `DayNum`,
      type: `number`,
      title: `Den`
    },

    weekday: {
      sql: `DayOfWeekNum`,
      type: `number`,
      title: `Den v týdnu`
    },

    hour: {
      sql: `HourNum`,
      type: `number`,
      title: `Hodina`
    },

    minute: {
      sql: `MinuteNum`,
      type: `number`,
      title: `Minuta`
    }
  }
});
