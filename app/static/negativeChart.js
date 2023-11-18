// Use JavaScript to fetch the dummy data for negative blood types
fetch('/plot_negative_data')
    .then(response => response.json())
    .then(data => {
        // Create the Highcharts line plot for negative blood types with animation
        var chart = Highcharts.chart('negativeChart', {
            chart: {
                type: 'line',
                zoomType: 'x', // Enable x-axis zoom
                panning: true, // Enable panning
                panKey: 'shift' // Hold Shift key to enable panning
            },
            title: {
                text: 'Negative Blood Types vs. Volume Inflow'
            },
            xAxis: {
                categories: data.months,
                crosshair: true,
                labels: {
                    enabled:true, // Enable labels
                }
            },
            yAxis: {
                title: {
                    text: 'Volume Inflow'
                }
            },
            series: [
                {
                    name: 'A-',
                    data: data.An,
                    visible: true, // Initially, this series is visible
                    events: {
                        click: function () {
                            toggleVisibility(this); // Toggle visibility of the series
                        }
                    },
                    marker: {
                        enabled: true // Disable markers
                    }
                },
                {
                    name: 'B-',
                    data: data.Bn,
                    visible: true, // Initially, this series is visible
                    events: {
                        click: function () {
                            toggleVisibility(this); // Toggle visibility of the series
                        }
                    },
                    marker: {
                        enabled: true // Disable markers
                    }
                },
                {
                    name: 'AB-',
                    data: data.ABn,
                    visible: true, // Initially, this series is visible
                    events: {
                        click: function () {
                            toggleVisibility(this); // Toggle visibility of the series
                        }
                    },
                    marker: {
                        enabled: true // Disable markers
                    }
                },
                {
                    name: 'O-',
                    data: data.On,
                    visible: true, // Initially, this series is visible
                    events: {
                        click: function () {
                            toggleVisibility(this); // Toggle visibility of the series
                        }
                    },
                    marker: {
                        enabled: true // Disable markers
                    }   
                }
            ]
        });

        // Function to toggle the visibility of a series
        function toggleVisibility(clickedSeries) {
            var tg = true;
            chart.series.forEach(function (series) {
                if (series.visible == false) {
                    tg = false;
                }
            });
            if (tg) {
                chart.series.forEach(function (series) {
                    if (series === clickedSeries) {
                        series.setVisible(true, true);
                    } else {
                        series.setVisible(false, true);
                    }
                });
            }
            else {
                chart.series.forEach(function (series) {
                    series.setVisible(true, true);
                });
            }
        }
    });
