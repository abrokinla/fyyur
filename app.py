#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from shutil import Error
from urllib.robotparser import RequestRate
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from sqlalchemy import false
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
import sys
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
db.init_app(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:12345@localhost:5432/fyyr'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date= dateutil.parser.parse(value)
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value
  if format == 'full':
    format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
    format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
  
  list_venue = []
  myareas = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)


  for area in myareas:
    avenue = Venue.query.filter(Venue.state == area.state).filter(Venue.city == area.city).all()
    data = []
    for venue in avenue:
      data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(db.session.query(Shows).filter(Shows.start_time > datetime.now()).all())
      })
      list_venue.append({
        "city": venue.city,
        "state": venue.state,
        "venues": data
      })

  
  
  return render_template('pages/venues.html', areas=list_venue);


@app.route('/venues/search/<search_item>', methods=['POST'])
def search_venues(search_item):
  search_term = request.form.get('search_term', '')
  result = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
  result_length = len(result)
  response = {
      "count": result_length,
      "data": result
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  past_shows = []
  upcoming_shows= []
  avenue = Venue.query.filter(Venue.id == venue_id).first()
  pastshows = db.session.query(Shows).filter(Shows.venue_id == venue_id).filter(Shows.start_time < datetime.now()).join(Artist, \
    Shows.artist_id == Artist.id).add_columns(Artist.id, Artist.name, Artist.image_link,Shows.start_time).all()
  upcomingshows = db.session.query(Shows).filter(Shows.venue_id == venue_id).filter(Shows.start_time > datetime.now()).join(Artist,\
     Shows.artist_id == Artist.id).add_columns(Artist.id, Artist.name,Artist.image_link, Shows.start_time).all()
  for showdata in pastshows:
    past_shows.append({
      "artist_id": showdata.id,
      "artist_name": showdata.name,
      "image_link": showdata.image_link,
      "start_time": str(showdata['4'])
    })
  for showdata in upcomingshows:
    upcoming_shows.append({
      "artist_id": showdata.id,
      "artist_name": showdata.name,
      "image_link": showdata.image_link,
      "start_time": str(showdata['4'])
    })
  if avenue is None:
    flash("Venue is not available, Please try again later")
    

  venuedata = {
    "id":  avenue.id,
    "name": avenue.name,
    "city": avenue.city,
    "state": avenue.state,
    "phone": avenue.phone,
    "address": avenue.address,
    "genres": [avenue.genres],
    "facebook_link": avenue.facebook_link,
    "image_link": avenue.image_link,
    "website_link": avenue.website_link,
    "seeking_talent": avenue.seeking_talent,
    "seeking_description": avenue.seeking_description,
    "past_shows": pastshows,
    "upcoming_shows": upcomingshows,
    "past_shows_count": len(pastshows),
    "upcoming_shows_count": len(upcomingshows)
    }
    
  
  return render_template('pages/show_venue.html', venue=venuedata)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    if request.method=='POST':

      name = request.form.get('name')
      city = request.form.get("city")
      state = request.form.get("state")
      address = request.form.get('address')
      phone = request.form.get('phone')
      genres = request.form.getlist('genres')
      image_link = request.form.get('image_link')
      facebook_link = request.form.get('facebook_link')
      website_link = request.form.get('website_link')
      seeking_talent = bool(request.form.get('seeking_talent'))
      seeking_description = request.form.get('seeking_description')

      venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres,\
         image_link=image_link, facebook_link=facebook_link, website_link=website_link, seeking_talent=seeking_talent,\
           seeking_description=seeking_description)
      db.session.add(venue)
      db.session.commit()
  except: 
    error = True
    db.session.rollback()
  finally:
    db.session.close()  # on successful db insert, flash success
  if error== True:
    flash('An error occurred. Venue '  + name +' could not be listed.')
  else:
    flash('Venue ' + name + ' was successfully listed!')
  
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    Venue.query.filter(venue_id).delete()
    db.session.commit()
  except:
    error = True
    db.session.rollnack()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error == True:
    flash("Could not delete venue!")

  
  
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
  artist = Artist.query.all()
  
  return render_template('pages/artists.html', artists=artist)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  result_length = len(result)
  results = {
      "count": result_length,
      "data": result
  }
  
  return render_template('pages/search_artists.html', results=results, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  pastshows = []
  upcomingshows = []
  artist = Artist.query.filter(Artist.id == artist_id).first()
  pastshow = db.session.query(Shows).filter(Shows.artist_id == artist_id).filter(Shows.start_time < datetime.now()).join(Venue, \
    Shows.venue_id == Venue.id).add_columns(Venue.id, Venue.name, Venue.image_link, Shows.start_time).all()
  upcomingshow = db.session.query(Shows).filter(Shows.venue_id == artist_id).filter(Shows.start_time > datetime.now()).join(Venue,\
     Shows.venue_id == Venue.id).add_columns(Venue.id, Venue.name,Venue.image_link, Shows.start_time).all()
  for show in pastshow:
    pastshows.append({
      'venue_id': show[1],
      'venue_name': show[2],
      'image_link': show[3],
      'start_time': str(show[4])
    })
  for show in upcomingshow:
    upcomingshows.append({
      'venue_id': show[1],
      'venue_name': show[2],
      'venue_link': show[3],
      'venue_time': str(show[4])
    })
  if artist is None:
    flash("Artist is not available!")


  artistdata = {
    "id":  artist.id,
    "name": artist.name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "genres": artist.genres.split(','),
    "facebook_link": artist.facebook_link,
    "image_link": artist.image_link,
    "website_link": artist.website_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "past_shows": pastshows,
    "upcoming_shows": upcomingshows,
    "past_shows_count": len(pastshows),
    "upcoming_shows_count": len(upcomingshows)
  }
  
  return render_template('pages/show_artist.html', artist=artistdata)

#  Update Artist
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  form_edit = Artist.query.filter(Artist.id == artist_id)
  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.image_link.data = artist.image_link
  form.facebook_link.data = artist.facebook_link
  form.website_link.data = artist.website_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  
  return render_template('forms/edit_artist.html', form=form, artist=form_edit)


# Edit artist
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  my_artist = Artist.query.filter(Artist.id==artist_id).first()
  form= ArtistForm(request.form)
  try:
    my_artist.name = form.name.data
    my_artist.city = form.city.data
    my_artist.state = form.state.data
    my_artist.phone = form.phone.data
    my_artist.genres = form.genres.data
    my_artist.image_link= form.image_link.data
    my_artist.facebook_link= form.facebook_link.data
    my_artist.website_link = form.website_link.data
    my_artist.seeking_talent = form.seeking_talent.data
    my_artist.seeking_description = form.seeking_description.data
    db.session.commit()
    flash('Record updated successfully')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info)
  finally:
    db.session.close()  
  if error:
    flash("An error occured. Your update was unsuccessful.")
  else:
    flash("Update successful!")
  
  return redirect(url_for('show_artist', artist_id=artist_id))


# Edit Venue
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  
  form = VenueForm()
  avenue = Venue.query.get(venue_id)  
  form_edit = Venue.query.filter(Venue.id == venue_id)
  form.name.data = avenue.name
  form.city.data = avenue.city
  form.state.data = avenue.state
  form.address.data= avenue.address
  form.phone.data = avenue.phone
  form.genres.data = avenue.genres
  form.image_link.data = avenue.image_link
  form.facebook_link.data = avenue.facebook_link
  form.website_link.data = avenue.website_link
  form.seeking_talent.data = avenue.seeking_talent
  form.seeking_description.data = avenue.seeking_description
 
  return render_template('forms/edit_venue.html', form=form, venue=form_edit)

@app.route('/venues/<int:venue_id>/edit', methods=['GET', 'POST'])
def edit_venue_submission(venue_id):
  my_venue = Venue.query.filter(Venue.id==venue_id).first()  
  form= VenueForm(request.form) 
  my_venue.name = form.name.data  
  my_venue.city = form.city.data  
  my_venue.state = form.state.data  
  my_venue.address = form.address.data  
  my_venue.phone = form.phone.data  
  my_venue.genres = form.genres.data  
  my_venue.image_link= form.image_link.data  
  my_venue.facebook_link = form.facebook_link.data  
  my_venue.website_link = form.website_link.data  
   
  my_venue.seeking_talent = form.seeking_talent.data  
  my_venue.seeking_description = form.seeking_description.data 
  if request.method == 'POST':# update Venue database
    db.session.commit() # succesful update
    flash('Artist ' + my_venue.name + ' has been updated successfully.')  
  else:    # Unsuccesful update        
    flash('There was an error. Artist ' + my_venue.name + ' was not updated.')

  

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')
    image_link = request.form.get('image_link')
    website_link = request.form.get('website_link')
    seeking_venue = bool(request.form.get('seeking_venue'))
    seeking_description = request.form.get('seeking_description')

    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website_link=website_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()    
  except: 
    error = True
    db.session.rollback()
  finally:
    db.session.close()  # on successful db insert, flash success
  if error==True:
    flash('An error occurred. Artist ' + name + ' could not be listed.')
  else:
    flash('Artist ' + name + ' was successfully listed!')   
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  shows = Shows.query.join(Artist, Artist.id == Shows.artist_id).join(Venue, Venue.id == Shows.venue_id).all()
  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time
    })
  # displays list of shows at /shows
  
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')

    show = Shows(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error == False:
    flash('Show was successfully listed!')
  # on successful db insert, flash success
  else:
    flash('An error occurred. Show could not be listed.')
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#--------------- -------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
