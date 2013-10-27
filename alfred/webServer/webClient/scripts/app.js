alfred = angular.module('alfred', ['ngRoute', 'ngAnimate'])
    .config(['$routeProvider', function($routeProvider){
        $routeProvider
            .when('/items', {
                templateUrl: 'views/items.html',
                controller: 'ItemCtrl'
            })
            .when('/cameras', {
                templateUrl: 'views/cameras.html',
            })
            .when('/bindings', {
                templateUrl: 'views/bindings.html',
            })
            .otherwise({redirectTo: '/items'})
    }])

    .factory('WebSocket', function($rootScope){
        $rootScope.connected = 'Connecting...'
        return {
            connect: function(){
                $this = this
                console.log('Trying to connect to WebSocket..')
                var socket = new WebSocket('ws://' + location.host + '/live');
                socket.onopen = function(){
                    console.log('Socket connected!');
                    $rootScope.connected = 'Connected'
                    $rootScope.$apply()
                }
                socket.onerror = function(event){ console.log('WebSocket error: ' + event);}
                socket.onclose = function(event){
                    $rootScope.connected = 'Connecting...'
                    $rootScope.$apply()
                    console.error('Socket closed, reconnecting in 5 seconds...')
                    setTimeout(function(){$this.connect()}, 5000)
                }
                socket.onmessage = function(msg){
                    // console.debug(msg);
                    $rootScope.$apply(
                        $this.onmessage(msg)
                    )
                }
            },
            onmessage: function(callback){}
        }
    })

alfred.run(function(WebSocket){
    WebSocket.connect();
})