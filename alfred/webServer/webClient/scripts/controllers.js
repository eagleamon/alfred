alfred.controller('ItemCtrl' , function($scope, $http, WebSocket){

    $scope.items = {}
    // Get first values
    // TODO: use angular resources
    $http.get('/api/items').
        success(function(data){
            angular.forEach(data, function(item){
                $scope.items[item.name] = item;
                if (item.time)
                    item.time = new Date(item.time);
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

// TODO: use angular resources
.controller('GraphCtrl', function($scope, $routeParams, $http, WebSocket){
    $scope.addPoint = function(){
        $scope.data.push(Math.floor(Math.random()*10))
    }

    WebSocket.onmessage = function(msg){
        msg = JSON.parse(msg.data);
        item = msg.topic.split('/').pop()
        if (item == $scope.item){
            payload = JSON.parse(msg.payload);

            // $scope.chart.series[0].addPoint(payload.value, true, true)
            $scope.data.push(payload.value);
            if ($scope.data.length>50)
                $scope.data.shift();
        }
    }


    $scope.item = {name: $routeParams.itemName};
    $scope.data = [];
    $scope.chart = {
        animation: {duration:800},
        title: {
            text: "Last values for " + $scope.item.name,
        },
        series: [{
            data: $scope.data,
            name: $scope.item.name,
            // marker: {enabled:false},
            animation:{duration:1000}
        }],
        yAxis:{
            title:{ text: $scope.item.unit }
        },

        legend: false,
        // useHighStocks: true
        loading: true
    }
    $http.get('/api/items/' + $scope.item.name).success(function(data){
        $scope.item = data
    })

    $http.get('/api/values/' + $scope.item.name).success(function(data){
        // $scope.chart.series[0].setVisible(false)

        angular.forEach(data, function(p){
            $scope.data.push(p.value)
        });
        $scope.chart.loading=false;
        // $scope.chart.series[0].setVisible(true, true)
    })


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
