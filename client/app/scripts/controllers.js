'use strict';

angular.module('alfred').controller('HmiCtrl', function($scope, Item, WebSocket, Commands) {
    $scope.items = {};

    // Listen on updates (TODO: only for items here)
    WebSocket.onmessage = function(msg) {
        var name = msg.topic.split('/').pop();
        if (name in $scope.items) {
            $scope.items[name].value = msg.value;
            $scope.items[name].time = new Date(msg.time);
        }
    };

    Item.query(function(data) {
        angular.forEach(data, function(d) {
            $scope.items[d.name] = d;
            if (d.time)
                d.time = new Date(d.time.$date);
        });
    });

    $scope.sendCommand = Commands.send;

    // Check if 'old' label should be displayed, 5h old by default
    $scope.older = function(litems, pAge) {
        var age = pAge || 1000 * 60 * 60 * 5,
            now = new Date(),
            res = false;

        angular.forEach(litems, function(item) {
            if ((item in $scope.items) && ($scope.items[item].time) && ((now - $scope.items[item].time) > age))
                res = true;
        });
        return res;
    };
    window.old = $scope.older;
})

.controller('ItemsCtrl', function($scope, Item, WebSocket, Commands, $modal, AlertService) {

    $scope.commands = {
        'switch': ['On', 'Off', 'Toggle'],
        'number': ['Increase', 'Decrease', 'Set']
    };

    // Get Items and parse dates
    $scope.items = {};
    Item.query(function(data) {
        angular.forEach(data, function(d) {
            $scope.items[d.name] = d;
            if (d.time)
                d.time = new Date(d.time.$date);
        });
    });

    // Listen on updates (TODO: only for items here)
    WebSocket.onmessage = function(msg) {
        var name = msg.topic.split('/').pop();
        if (name in $scope.items) {
            $scope.items[name].value = msg.value;
            $scope.items[name].time = new Date(msg.time);
        }
    };

    $scope.showDeleteDlg = function(itemId, itemName) {
        $modal.open({
            templateUrl: 'deleteDialog.html',
        })
            .result.then(function() {
                Item.get({
                    _id: itemId
                }, function(item) {
                    item.$delete(function() {
                        delete $scope.items[itemName];
                    }, function(error) {
                        AlertService.add({
                            msg: 'Error while deleting: ' + error.data,
                            type: 'danger'
                        });
                    });
                });
            }, function() {
                console.log('Delete canceled');
            });
    };

    $scope.sendCommand = Commands.send;
})

.controller('PluginCtrl', function($scope, $http, Plugin, AlertService) {
    Plugin.query().success(function(data) {
        $scope.available = data.available;
        $scope.installed = data.installed;
    });
    $scope.isc = true;

    $scope.install = function(name) {
        Plugin.install(name).success(function() {
            $scope.installed[name] = {
                active: false,
                config: {},
                autoStart: false
            };
            $scope.available.splice($scope.available.indexOf(name), 1);
        }).error(function(data) {
            AlertService.add({
                msg: data,
                type: 'danger',
                timeout: 1500
            });
        });
    };

    $scope.uninstall = function(name) {
        Plugin.uninstall(name).success(function() {
            delete $scope.installed[name];
            $scope.available.push(name);
        });
    };

    $scope.toggle = function(name) {
        if ($scope.installed[name].active)
            $scope.stop(name);
        else
            $scope.start(name);
    };

    $scope.start = function(name) {
        Plugin.start(name).success(function() {
            $scope.installed[name].active = true;
        }).error(function(data) {
            AlertService.add({
                msg: data,
                type: 'danger',
                timeout: 1500
            });
        });
    };

    $scope.stop = function(name) {
        Plugin.stop(name).success(function() {
            $scope.installed[name].active = false;
        }).error(function(data) {
            AlertService.add({
                msg: data,
                type: 'danger',
                timeout: 1500
            });
        });
    };

    $scope.autoStart = function(name) {
        Plugin.save(name, $scope.installed[name]);
    };

    // bean.on(window, 'keydown', function(e){
    //     e.preventDefault();
    //     var keyCode = e.keyCode;

    //     var match = map[keyCode];
    //     if(match){
    //         console.log(match)
    //         sendInputCommand(match);
    //     }
    //     else{
    //         console.log(keyCode);
    //     }
    // });

    // var map = {
    //     37: {command:'Input.Left', params:{}},
    //     39: {command:'Input.Right', params:{}},
    //     38: {command:'Input.Up', params:{}},
    //     40: {command:'Input.Down', params:{}},
    //     13: {command:'Input.Select', params:{}},
    //     8:  {command:'Input.Back', params:{}},
    //     77: {command:'Input.ShowOSD'},
    //     27: {command:'Input.ExecuteAction', params: {action: 'close'}},
    //     67: {command:'Input.ContextMenu', params:{}},
    //     80: {command:'Player.PlayPause', params:{playerid:1}},
    //     32: {command:'Player.PlayPause', params:{playerid:1}},
    //     83: {command:'Player.Stop', params:{playerid:1}},
    //     48: {command:'Application.SetMute', params:{}}

    // };

    // function sendInputCommand(match){
    //     var data = {
    //         jsonrpc: "2.0",
    //         method: match.command,
    //         params: match.params,
    //         id: 1
    //     }
    //     ws.send(JSON.stringify(data));
    // }
    // window.send = sendInputCommand

    // var ws = new WebSocket('ws://htpc:9090/jsonrpc');
    // ws.onopen = function() {
    //     console.log('open');
    // };
    // ws.onclose = function(evt) {
    //     console.log('closed')
    // };
    // ws.onmessage = function(evt) {
    //     console.log(evt.data)
    // };
    // ws.onerror = function(evt) {
    //     console.log(evt.data)
    // };
})

.controller('GraphCtrl', function($scope, $routeParams, WebSocket, Item, $resource) {

    WebSocket.onmessage = function(msg) {
        var item = msg.topic.split('/').pop();
        if (item === $scope.item.name) {
            $scope.data.push([new Date(msg.time).getTime(), msg.value]);
            if ($scope.data.length > 50)
                $scope.data.shift();
        }
    };
    window.item = Item;

    $scope.item = Item.get({
        _id: $routeParams._id
    }, function() {
        $scope.data = [];
        $scope.chart = {
            chart: {
                zoomType: 'x',
            },
            animation: {
                duration: 800
            },
            title: {
                text: 'Last day values for ' + $scope.item.name,
            },
            series: [{
                data: $scope.data,
                // step: 'left',
                name: $scope.item.name + ($scope.item.unit ? ' (' + $scope.item.unit + ')' : ''),
                // marker: {enabled:false},
                animation: {
                    duration: 1000
                }
            }],
            xAxis: {
                type: 'datetime'
            },
            yAxis: {
                title: {
                    text: $scope.item.unit
                }
            },
            tooltip: {
                shared: true
            },
            legend: false,
            // useHighStocks: true
            loading: true
        };

        $resource('/api/v1/item/:item_id/values').query({
            'item_id': $scope.item._id.$oid
        }, function(data) {
            if ($scope.item.type === 'switch')
                $scope.chart.series[0].step = 'left';

            angular.forEach(data, function(d) {
                $scope.data.push([getTimeStamp(d._id.$oid), typeof(d.value) === 'number' ? d.value : d.value || 0]);
            });
            $scope.chart.loading = false;
        });
    });

    var getTimeStamp = function(_id) {
        return parseInt(_id.toString().slice(0, 8), 16) * 1000;
    };

})

.controller('EditItemCtrl', function($scope, $routeParams, $location, AlertService, Item) {
    if ($routeParams._id)
        $scope.item = Item.get({
            '_id': $routeParams._id
        });
    else
        $scope.item = new Item();

    $scope.types = ['number', 'switch', 'string'];

    $scope.submit = function() {
        delete $scope.item.time; // Do not update those ones here :)
        delete $scope.item.value;

        if ($scope.item.groups && !$scope.item.groups.push) // If it is not an array
            $scope.item.groups = $scope.item.groups.split(',');

        if ($scope.item._id) {
            $scope.item.$update(function() {
                $location.path('/items');
            }, function(err) {
                AlertService.add({
                    msg: 'Error while updating: ' + err.data,
                    type: 'danger'
                });
            });
        } else {
            $scope.item.$save(function() {
                $location.path('/items');
            }, function(err) {
                AlertService.add({
                    msg: 'Error while saving: ' + err.data,
                    type: 'danger'
                });
            });
        }
    };
})


.controller('AuthCtrl', function($scope, $cookies) {
    $scope.user = {
        username: $cookies.username || null
    };
})

.controller('AlertCtrl', function($scope, AlertService) {
    $scope.alerts = AlertService.alerts;
    $scope.close = AlertService.close;
})

.controller('ConfigCtrl', function($scope, Config, $location, Item, AlertService) {
    $scope.settings = Config.get();

    $scope.itemsOptions = {
        multiple: true,
        simple_tags: true,
        closeOnSelect: false,
        tags: function() {
            return $scope.items;
        },
        createSearchChoice: function() {
            return null;
        },
    };

    $scope.submit = function() {
        var ssc = $scope.settings.config;
        ssc.http.debug = ssc.http.debug || ssc.http.debug.toLowerCase() === 'true';

        if (!ssc.items.pop)
            ssc.items = ssc.items.split(',').map(function(l) {
                return l.trim();
            });
        if (!ssc.persistence.items.pop)
            ssc.persistence.items = ssc.persistence.items.split(',').map(function(l) {
                return l.trim();
            });
        if (!ssc.persistence.groups.pop)
            ssc.persistence.groups = ssc.persistence.groups.split(',').map(function(l) {
                return l.trim();
            });

        $scope.settings.$update(function(res) {
            if (res.error)
                AlertService.add({
                    msg: 'Error while updating: ' + res.error,
                    type: 'danger'
                });
            else
                $location.path('/');
        }, function(err) {
            var str = err.data.split('(').pop();
            str = str.trim().substring(0, str.length - 2);
            AlertService.add({
                msg: 'Error while updating: ' + str,
                type: 'danger'
            });
        });
    };
});
