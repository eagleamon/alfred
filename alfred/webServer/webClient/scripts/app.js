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