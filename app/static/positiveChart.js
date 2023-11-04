// Use JavaScript to fetch the dummy data for positive blood types
fetch('/plot_positive_data')
    .then(response => response.json())
    .then(data => {
        // Create the Highcharts column chart for positive blood types with animation
        var chart = Highcharts.chart('positiveChart', {
            chart: {
                type: 'line',
                zoomType: 'x', // Enable x-axis zoom
                panning: true, // Enable panning
                panKey: 'shift', // Hold Shift key to enable panning
                backgroundColor: 'rgba(150, 15, 100, 0.2)', // Set background color with transparency
                borderWidth: 2, // Add a border to the chart
                borderColor: 'Red' // Set border color
            },
            title: {
                text: 'Positive Blood Types vs. Volume Inflow'
            },
            xAxis: {
                categories: data.dates,
                crosshair: true,
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
                        enabled: false // Disable markers
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
                        enabled: false // Disable markers
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
                        enabled: false // Disable markers
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
                        enabled: false // Disable markers
                    }   
                }
            ],
            plotOptions: {
                series: {
                    animation: {
                        duration: 2500 // Set the animation duration (milliseconds)
                    }
                }
            }
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
