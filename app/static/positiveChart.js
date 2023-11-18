// Use JavaScript to fetch the dummy data for positive blood types
fetch('/plot_positive_data')
    .then(response => response.json())
    .then(data => {
        // Create the Highcharts column chart for positive blood types with animation
        console.log(data)
        var chart = Highcharts.chart('positiveChart', {
            chart: {
                type: 'line',
                zoomType: 'x', // Enable x-axis zoom
                panning: true, // Enable panning
                panKey: 'shift', // Hold Shift key to enable panning
            },
            title: {
                text: 'Positive Blood Types vs. Volume Inflow'
            },
            xAxis: {
                categories: data.months,
                crosshair: true,
                labels: {
                    enabled:true // Enable labels
                }
            },
            yAxis: {
                title: {
                    text: 'Volume Inflow'
                }
            },
            series: [
                {
                    name: 'A+',
                    data: data.Ap,
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
                    name: 'B+',
                    data: data.Bp,
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
                    name: 'AB+',
                    data: data.ABp,
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
                    name: 'O+',
                    data: data.Op,
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
