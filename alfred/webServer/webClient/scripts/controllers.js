alfred.controller('ItemCtrl' , function($scope, Item,  WebSocket){

    $scope.items = {}
    Item.query(function(data){
        angular.forEach(data, function(d){
            $scope.items[d.name] = d;
            d.time = new Date(d.time.$date)
        })
    })

    // Listen on updates (TODO: only for items here)
    WebSocket.onmessage = function(msg){
        msg = JSON.parse(msg.data);
        payload = JSON.parse(msg.payload)
        name = msg.topic.split('/').pop();
        if (name in $scope.items){
            $scope.items[name].value = payload.value;
            $scope.items[name].time = new Date(payload.time);
        }
    }
})

.controller('GraphCtrl', function($scope, $routeParams, WebSocket, Item, $resource){

    WebSocket.onmessage = function(msg){
        msg = JSON.parse(msg.data);
        item = msg.topic.split('/').pop()
        if (item == $scope.item.name){
            payload = JSON.parse(msg.payload);
            $scope.data.push([new Date(payload.time).getTime(), payload.value]);
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
        return parseInt(_id.toString().slice(0,8), 16)*1000
        // return parseInt(_id.toString().slice(0,8), 16) - (new Date().getTimezoneOffset()*1000);
    }

})

.controller('EditItemCtrl', function($scope, $routeParams, Item){
    // $scope.item = Item.get({'name': $routeParams.itemName})
    $scope.item = new Item({'name': 'Rand'});
    $scope.item.$save()
    // $scope.item.name = "Rand";
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
