alfred.controller('HmiCtrl', function($scope, Item, WebSocket, Commands){
    $scope.items = {}
    Item.query(function(data){
        angular.forEach(data, function(d){
            $scope.items[d.name] = d;
        })
    })

    // $scope.sendCommand = Commands.send
    $scope.sendCommand = function(){
        console.log('ok')
    }

    // Listen on updates (TODO: only for items here)
    WebSocket.onmessage = function(msg){
        name = msg.topic.split('/').pop();
        if (name in $scope.items){
            $scope.items[name].value = msg.value;
            $scope.items[name].time = new Date(msg.time);
        }
    }
})

.controller('ItemCtrl' , function($scope, Item,  WebSocket, Commands,  $modal){

    $scope.commands={
        'switch': ['On', 'Off', 'Toggle'],
        'number': ['Increase', 'Decrease', 'Set']

    }

    $scope.items = {}
    Item.query(function(data){
        angular.forEach(data, function(d){
            $scope.items[d.name] = d;
            if (d.time)
                d.time = new Date(d.time.$date)
        })
    })

    // Listen on updates (TODO: only for items here)
    WebSocket.onmessage = function(msg){
        name = msg.topic.split('/').pop();
        if (name in $scope.items){
            $scope.items[name].value = msg.value;
            $scope.items[name].time = new Date(msg.time);
        }
    }

    $scope.showDeleteDlg = function(itemId, itemName){
        $modal.open({
            templateUrl:'deleteDialog.html',
        })
        .result.then(function(){
            var i = Item.get({_id:itemId}, function(item){
                item.$delete(function(res){
                    if (res.error)
                        AlertService.add({msg: 'Error while deleting: ' + res.error, type:'danger'})
                    else
                        delete $scope.items[itemName]
                })
            })
        },function(){
        })
    }

    $scope.sendCommand = Commands.send
})

.controller('BindingCtrl', function($scope){
    bean.on(window, 'keydown', function(e){
        e.preventDefault();
        var keyCode = e.keyCode;

        var match = map[keyCode];
        if(match){
            console.log(match)
            sendInputCommand(match);
        }
        else{
            console.log(keyCode);
        }
    });

    var map = {
        37: {command:'Input.Left', params:{}},
        39: {command:'Input.Right', params:{}},
        38: {command:'Input.Up', params:{}},
        40: {command:'Input.Down', params:{}},
        13: {command:'Input.Select', params:{}},
        8:  {command:'Input.Back', params:{}},
        77: {command:'Input.ShowOSD'},
        27: {command:'Input.ExecuteAction', params: {action: 'close'}},
        67: {command:'Input.ContextMenu', params:{}},
        80: {command:'Player.PlayPause', params:{playerid:1}},
        32: {command:'Player.PlayPause', params:{playerid:1}},
        83: {command:'Player.Stop', params:{playerid:1}},
        48: {command:'Application.SetMute', params:{}}

    };

    function sendInputCommand(match){
        var data = {
            jsonrpc: "2.0",
            method: match.command,
            params: match.params,
            id: 1
        }
        ws.send(JSON.stringify(data));
    }
    window.send = sendInputCommand

    var ws = new WebSocket('ws://htpc:9090/jsonrpc');
    ws.onopen = function() {
        console.log('open');
    };
    ws.onclose = function(evt) {
        console.log('closed')
    };
    ws.onmessage = function(evt) {
        console.log(evt.data)
    };
    ws.onerror = function(evt) {
        console.log(evt.data)
    };
})

.controller('GraphCtrl', function($scope, $routeParams, WebSocket, Item, $resource){

    WebSocket.onmessage = function(msg){
        item = msg.topic.split('/').pop()
        if (item == $scope.item.name){
            $scope.data.push([new Date(msg.time).getTime(), msg.value]);
            if ($scope.data.length>50)
                $scope.data.shift();
        }
    }

    $scope.item = Item.get({_id: $routeParams._id}, function(){
        $scope.data = [];
        $scope.chart = {
            chart:{
                zoomType: 'x'
            },
            animation: {duration:800},
            title: {
                text: "Last day values for " + $scope.item.name,
            },
            series: [{
                data: $scope.data,
                name: $scope.item.name + ($scope.item.unit ? ' (' + $scope.item.unit + ')': ''),
                // marker: {enabled:false},
                animation:{duration:1000}
            }],
            xAxis:{
                type: 'datetime'
            },
            yAxis:{
                title:{ text: $scope.item.unit }
            },
            tooltip: {
                shared: true
            },
            legend: false,
            // useHighStocks: true
            loading: true
        }

        $resource('/api/values/item_id/:item_id').query({'item_id': $scope.item._id.$oid}, function(data){
            angular.forEach(data, function(d){
                $scope.data.push([getTimeStamp(d._id.$oid), d.value])
            })
            $scope.chart.loading = false;
        })
    });

    getTimeStamp = function(_id){
        return parseInt(_id.toString().slice(0,8), 16)*1000;
    }

})

.controller('EditItemCtrl', function($scope, $routeParams, $location, AlertService, Item){
    $scope.item = Item.get({'_id': $routeParams._id})
    $scope.types = ['number', 'switch', 'string']

    $scope.submit = function(){
        delete $scope.item.time // Do not update those ones here :)
        delete $scope.item.value

        if ($scope.item.groups && !$scope.item.groups.push) // If it is not an array
            $scope.item.groups = $scope.item.groups.split(',')

        $scope.item.$update(function(res){
            if (res.error)
                AlertService.add({msg: "Error while updating: " + res.error, type:'danger'})
            else
                $location.path('/')
        })
    }
})

.controller('LoginCtrl', function($scope, $location, AlertService, Auth){
    $scope.login = function(){
        Auth.login($scope.username, $scope.password)
        .success(function(data){
            AlertService.add({msg: Auth.username + ", you've been logged in", type:'success', timeout: 2000})
            $location.path('/')
        })
        .error(function(data){
            AlertService.add({msg: "Bad username and/or password", type:'danger', timeout: 1500})
        })
    }
})

.controller('AlertCtrl', function($scope, AlertService){
    $scope.alerts = AlertService.alerts;
    $scope.close = AlertService.close;
})
