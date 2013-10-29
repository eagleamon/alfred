alfred.controller('ItemCtrl' , function($scope, $http, WebSocket){

    // Get first values
    // TODO: use angular resources
    $http.get('api/items').
        success(function(data){
            $scope.items = data;
            window.items = data;
            for (var item in $scope.items)
                if ($scope.items[item].time)
                    $scope.items[item].time = new Date($scope.items[item].time);
        })

    // Listen on updates (TODO: only for items here)
    WebSocket.onmessage = function(msg){
        msg = JSON.parse(msg.data);
        payload = JSON.parse(msg.payload)
        name = msg.topic.split('/').pop();
        $scope.items[name].value = payload.value;
        $scope.items[name].time = new Date(payload.time);
    }
})

.controller('GraphCtrl', function($scope, $routeParams, WebSocket){
    $scope.item = $routeParams.itemName;
    $scope.data = [];

    $scope.addPoint = function(){
        $scope.data.push(Math.floor(Math.random()*10))
    }

    WebSocket.onmessage = function(msg){
        msg = JSON.parse(msg.data);
        payload = JSON.parse(msg.payload);
        $scope.data.push(payload.value);
        if ($scope.data.length>50)
            $scope.data.shift();
    }

    $scope.chart = {
        title: {
            text: "Last values of " + $scope.item,
        },
        series: [{
            data: $scope.data,
            name: $scope.item
        }],
        legend: false
        // useHighStocks: true
    }
})
