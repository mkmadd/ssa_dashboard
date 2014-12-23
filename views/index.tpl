%# Bottle template
%# Test

<!DOCTYPE html>
<head>
    <title>Need Snappier Title</title>
    <meta http-equiv="refresh" content="900">

    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css">
    
    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap-theme.min.css">

    <link rel="stylesheet" type="text/css" href="{{ url('static', path='test_template.css') }}">

    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>    

    <!-- Latest compiled and minified JavaScript -->
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/js/bootstrap.min.js"></script>
    
%#    <script src="{{ url('static', path='test_javascript.js') }}"></script>
</head>
<body>
    <main class="container-fluid">
    %i = 0
    %for store in stores:
        %if i % 4 == 0:
            <div class="row">
        %end
        <div class="col-md-3">
            <div class="row">
                <div class="col-md-8">
                    <h4>{{store['store_name']}}</h4>
                </div>
                <div class="col-md-4">
                    <div class="row skinny-row">
                    </div>
                    <div class="row no-margin-b">
                        <div class="col-md-12 small-font">
                            <span id="time" class="{{'bg-blink' if store['time_expired'] else ''}}">{{store['last_update_time']}}</span>
                        </div>
                    </div>
                    <div class="row no-margin-b">
                        <div class="col-md-12 tiny-font">
                            <span id="date" class="{{'bg-blink' if store['date_expired'] else ''}}">{{store['last_update_date']}}</span>
                        </div>
                    </div>
                </div>
            </div>
            %for tank in store['tanks']:
                <div class="row">
                    <div class="col-md-4">
                        <div class="row no-margin-b">
                            <div class="col-md-12 no-margin-b">
                                <meter class="product-meter" min="0.0" low="0.25" optimum="0.75" high="0.5" max="1.0" value="{{tank['capacity']}}"></meter>
                            </div>
                        </div>
                        <div class="row no-margin-t">
                            <div class="col-md-12">
                                <meter class="water-meter" min="0.0" low="50" optimum="25" high="100" max="200.0" value="{{tank['water_vol']}}"></meter>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-8 tank-name">
                        {{'{0} ({1})'.format(tank['tank_name'], tank['product_name'])}}
                    </div>
                </div>
            %end
        </div>
        %if i % 4 == 3:
            </div>
        %end
        %i += 1
    %end
    </table>
    </main>
</body>