alfred = angular.module('alfred', ['ngRoute', 'ngAnimate', 'ui.bootstrap', 'highcharts-ng'])
    .config(['$routeProvider', '$httpProvider', function($routeProvider, $httpProvider){
        $routeProvider
            .when('/items', {
                templateUrl: 'views/items.html',
                controller: 'ItemCtrl'
            })
            .when('/graph/:itemName', {
            	templateUrl: 'views/graph.html',
            	controller: 'GraphCtrl'
            })
            .when('/cameras', {
                templateUrl: 'views/cameras.html',
            })
            .when('/bindings', {
                templateUrl: 'views/bindings.html',
            })
            .when('/login',{
                templateUrl: 'views/login.html',
                controller: 'LoginCtrl'
            })
            .otherwise({redirectTo: '/items'})


        // If the server needs an authentication, redirect to the login page
        $httpProvider.interceptors.push(function($q, $location){
            return {
                'responseError': function(rejection){
                    if (rejection.status == 401)
                        $location.path("/login")
                    return $q.reject(rejection)
                }
            }
        });

    }])

    .factory('WebSocket', function($rootScope){
        $rootScope.connected = 'Connecting...'
        return {
            connect: function(){
                var $this = this;
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

    // Service to handle atuthentication against backend validation
    .factory('Auth', function($http){
        return {
            username: '',
            login: function(username, password){
                var $this = this;
                return $http.post('/auth/login', {username:username, password: password})
                    .success(function(data){
                        $this.username = username
                })
            }
        }
    })

    // Simple service to handle the alerts
    .factory('AlertService', function($timeout){
        return {
            alerts:[],

            // Timeout to automatically remove alerts after a defined period
            add: function(alert){
                var $this = this;
                this.alerts.push(alert);
                if ('timeout' in alert){
                    $timeout(function() {
                        $this.close($this.alerts.length-1)
                    }, alert.timeout);
                }
            },

            close: function(index){
                this.alerts.splice(index, 1);
            }
        }
    })

    .directive('showOnHover', function(){
        return {
            link: function(scope, element, attrs){
                element.css('visibility', 'hidden')
                element.parent().parent().bind('mouseenter', function(){
                    element.css('visibility','visible');
                });
                element.parent().parent().bind('mouseleave', function(){
                    element.css('visibility','hidden');
                })
            }
        }
    })

alfred.run(function($rootScope, WebSocket){
    WebSocket.connect();
})
