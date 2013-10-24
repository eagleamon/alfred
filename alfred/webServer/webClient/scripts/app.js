alfred = angular.module('alfred', []).config(['$routeProvider', function($routeProvider){
    $routeProvider.
        when('/items', {
            templateUrl: 'views/items.html',
            controller: 'ItemCtrl'
        }).
        when('/cameras', {

        }).
        otherwise({redirectTo: '/items'})
}])

alfred.factory('socket', function($rootScope){
    var socket = new WebSocket('ws://' + location.host + '/live');
    return {
        on: function(callback) {
            socket.onmessage = function(msg){
                console.log(msg)
                $rootScope.$apply(function(){
                    callback(msg)
                });
            };
        },
    }
})