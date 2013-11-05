alfred = angular.module('alfred', ['ngRoute', 'ngResource', 'ngAnimate', 'ui.bootstrap', 'highcharts-ng', 'angularMoment'])
    .config(['$routeProvider', '$httpProvider', function($routeProvider, $httpProvider){
        $routeProvider
            .when('/items', {
                templateUrl: 'views/items.html',
                controller: 'ItemCtrl'
            })
            .when('/editItem/:_id',{
                templateUrl: 'views/editItem.html',
                controller: 'EditItemCtrl'
            })
            .when('/graph/:_id', {
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
                console.info('Trying to connect to WebSocket..')
                var socket = new WebSocket('ws://' + location.host + '/live');
                socket.onopen = function(){
                    console.info('Socket connected!');
                    $rootScope.connected = 'Connected'
                    $rootScope.$apply()
                }
                socket.onerror = function(event){ console.info('WebSocket error: ' + event);}
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
    .factory('Auth', function($http, $location, $rootScope){
        return {
            username: '',
            login: function(username, password){
                var $this = this;
                return $http.post('/auth/login', {username:username, password: password})
                    .success(function(data){
                        $this.username = username
                })
            },
            logout: function(){
                var $this = this;
                $http.get('/auth/logout')
                    .success(function(){
                        $this.username = null;
                        $location.path('/')
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

    .factory('Item', function($resource){
        return $resource('/api/items/:_id')
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

alfred.run(function($rootScope, WebSocket, Auth){
    Highcharts.setOptions({                                            // This is for all plots, change Date axis to local timezone
                global : {
                    useUTC : false
                }
            });

    $rootScope.logout = Auth.logout
    WebSocket.connect();
})
