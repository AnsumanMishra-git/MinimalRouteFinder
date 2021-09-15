import pandas as pd
from math import cos, asin, sqrt
import streamlit as st
import base64
import gspread
from google.oauth2 import service_account
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import geocoder


    
st.write("""
# Minimum Route for The SalesPerson

**NOTE :** The distance is calculated using **Haversine Formula** which may vary from the actual distance.

""")
st.write("""


        """)

# Assign credentials ann path of style sheet
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"],
)

client = gspread.authorize(creds)
sheet = client.open('MERGED').sheet1

if "Bindex" not in st.session_state:
        st.session_state.Bindex=[]

if "Id" not in st.session_state:
        st.session_state.Id=[]

def reset_data():
    with st.spinner(text="Resetting Your Data..."):
                df['Visited']=0
                df['Blacklisted']=0
                set_with_dataframe(sheet, df)

def update_data():
    with st.spinner(text="Updating Your Data..."):
                    for ids in st.session_state.Id:
                        sheet.update_cell(ids+1, 10 ,1)
                    for bids in st.session_state.Bindex:
                        sheet.update_cell(bids+1, 11 ,1)
                    st.session_state.Id=[]
                    st.session_state.Bindex=[]
    st.success("Done.")

with st.spinner(text="Please wait , Fetching the Data..."):
    df = pd.DataFrame(sheet.get_all_records())

def load_data(view):
    if view=='Minimal Route Finder':
        return df[df['Blacklisted']==0]
    elif view=='Visited':
        return df[df['Visited']==1]
    elif view=='Blacklisted':
        return df[df['Blacklisted']==1]


def filedownload(df,filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    #filename = "minimalRoute_Day-"+user_day+".csv"
    href = f'<a href="data:file/csv;base64,{b64}" download={filename}>Download CSV File</a>'
    return href

st.sidebar.header('Click Below if you want to reset all your progress.')
if st.sidebar.button('Reset'):
    reset_data()

st.header("""

          Click below if you have confirmed all your trips !
          """)

if st.button('Update Sheet'):
    update_data()

df['Marked']=0
counts=df['Type'].value_counts()
st.sidebar.header('User Input Features')
view=['Minimal Route Finder','Visited','Blacklisted']
selected_view = st.sidebar.selectbox('View', view)

with st.spinner(text="Fetching Your Coordinates..."):
    g = geocoder.ip('me')
    my_lat = g.latlng[0]
    my_lon = g.latlng[1]
    
st.header('Enter coordinates of your starting point')
coord = "13.945281,77.7364"
coordinate = st.text_area("Enter latitude and longitude separated by a comma. Eg: 13.945281,77.7364 ", coord, height=25)
coordinates=coord.split(',')
latitude=float(coordinates[0])
longitude=float(coordinates[1])

st.subheader('Click below if you dont know the coordinates of your current location ')
if st.checkbox('Get my current location'):
    latitude=my_lat
    longitude=my_lon
    
    
st.write("""

""")

selected_data = load_data(selected_view)
selected_data=selected_data.sort_values(by=['Latitude','Longitude'])
selected_data=selected_data.reset_index(drop=True)

if selected_view=='Visited':
    st.header('Visited Stores')
    st.dataframe(selected_data.iloc[:,:-3])
    st.markdown(filedownload(selected_data,"Visited_Stores.csv"), unsafe_allow_html=True)

elif selected_view=='Blacklisted':
    st.header('Blacklisted Stores')
    st.dataframe(selected_data.iloc[:,:-3])
    st.markdown(filedownload(selected_data,"BlackListed_Stores.csv"), unsafe_allow_html=True)



if selected_view=='Minimal Route Finder':
    st.header('Enter the number of trips per day you want')
    tpd = 12
    num = int(st.text_area("trips per day", tpd, height=25))
    
    selected_loc = st.sidebar.text_area('Search By Location', height=20)  
    
    sorted_unique_type = sorted(selected_data.Type.unique())
    selected_type = st.sidebar.multiselect('Search By Type', sorted_unique_type)

    sorted_unique_name = selected_data.Name.unique()
    selected_name = st.sidebar.multiselect('Blacklist Names', sorted_unique_name)

    if selected_name :
        for i in range(0,len(df)):
            if df['Name'][i] in selected_name:
                st.session_state.Bindex.append(df['id'][i])
                df['Blacklisted'][i]=1
    else:
        st.session_state.Bindex=[]

    # Filtering data
    df1 = selected_data[(selected_data.Type.isin(selected_type)) & ~(selected_data.Name.isin(selected_name))]
    df1=df1.reset_index(drop=True)
    df1['Marked']=0
    
    loc_list=[]
    for i in range(0,len(df1)):
        if (str(df1['Address'][i]).find(selected_loc) != -1):
            loc_list.append(df1['Address'][i])
            
    df_selected_type=df1[df1.Address.isin(loc_list)]
    df_selected_type=df_selected_type.reset_index(drop=True)
    
    if len(df_selected_type)>1000:
        df_selected_type = df_selected_type[(df_selected_type['Latitude']>float(latitude)-0.85) & (df_selected_type['Latitude']<float(latitude)+0.85) &
                              (df_selected_type['Longitude']>float(longitude)-0.85) & (df_selected_type['Longitude']<float(longitude)+0.85)]
        df_selected_type=df_selected_type.reset_index(drop=True)
    
    
    
    def distance(lat1, lon1, lat2, lon2):
        p = 0.017453292519943295 # conversion to radians factor
        a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2  #a = haversine
        return 12742 * asin(sqrt(a))  #diameter of earth = 12742km


    #find the store closest to the current location

    def next(lat,lon):
        min_dist = 10000.0
        min_index=-1
        for i in range(0,len(df_selected_type)):
            if (df_selected_type['Marked'][i]==0) & (df_selected_type['Blacklisted'][i]==0) & (df_selected_type['Visited'][i]==0):
                if distance(lat,lon,df_selected_type['Latitude'][i],df_selected_type['Longitude'][i]) < min_dist :
                    min_dist=distance(lat,lon,df_selected_type['Latitude'][i],df_selected_type['Longitude'][i])
                    min_index=i
                    if min_dist==0.0:
                        return min_index
        return min_index
    st.write("""

                 """)


    #latitude  =13.945281
    #longitude=77.7364
    # display the index of the next num stores that he should go to
    d = pd.DataFrame()
    with st.spinner(text="Finding stores near you..."):
        for day in range(1,(len(df_selected_type)//num)+2):

            ind=[]
            lat=float(latitude)
            lon=float(longitude)
            index=next(lat,lon)

            while len(ind) != num and index !=-1:
                df_selected_type['Marked'][index]=1
                ind.append(index)
                lat=df_selected_type['Latitude'][index]
                lon=df_selected_type['Longitude'][index]
                index=next(lat,lon)


            lat=float(latitude)
            lon=float(longitude)
            for i in ind:
                dist= distance(lat,lon,df_selected_type['Latitude'][i],df_selected_type['Longitude'][i])
                lat=df_selected_type['Latitude'][i]
                lon=df_selected_type['Longitude'][i]
                d = d.append({"ID":df_selected_type['id'][i],"Company Name":df_selected_type['Name'][i],"Phone":df_selected_type['Phone'][i],
                              "Link":df_selected_type['Link'][i],"Address":df_selected_type['Address'][i],
                                 "Pin Code":df_selected_type['Pincode'][i],"Distance":dist,
                             "Latitude":df_selected_type['Latitude'][i],"Longitude":df_selected_type['Longitude'][i],
                             "Visited":df_selected_type['Visited'][i],"Blacklisted":df_selected_type['Blacklisted'][i]},ignore_index=True)


    st.write("""

                 """)

    

    st.header('INPUT (Origin Location)')
    st.write("Your Current Location( " +str(latitude) + " , " + str(longitude) +" )")

    #user_day='2'
    #day=2
    st.header('OUTPUT (The Minimum Route)')
    st.subheader(str(len(df_selected_type))+ " stores found.")
    if(len(df_selected_type)>0):
            display = pd.DataFrame()

            display=d[d['Visited']==0].copy()
            display=display.reset_index(drop=True)
            st.session_state.Id=[]
            for  j in range(0,num):
                if(j<len(display)):
                   st.session_state.Id.append(int(display['ID'][j]))
            cols=['Address', 'Company Name', 'Distance', 'Link', 'Phone','Pin Code','Latitude','Longitude']
            st.dataframe(display[cols][0:num])
            st.markdown(filedownload(display[cols][0:num],"Minimal_Route.csv"), unsafe_allow_html=True)
            st.subheader("Detailed trip info -")
            for i in range (0,num):
                if i<len(display):
                    st.subheader("Trip - "+str(i+1))
                    st.write('Company Name - '+ str(display['Company Name'][i]))
                    st.write('Address - '+ str(display['Address'][i]))
                    st.write('Pin Code - '+ str(display['Pin Code'][i]))
                    st.write('Distance from current trip - '+ str(round(display['Distance'][i],3))+' KM')
                    lati=display['Latitude'][i]
                    longi=display['Longitude'][i]
                    url = '[Go to Maps](https://maps.google.com/?ll='+str(lati)+','+str(longi)+')'
                    st.markdown(url, unsafe_allow_html=True)


                else:
                    st.write("""

                             """)
                    st.subheader("You no longer have any stores to visit . Please change the type of store you want to visit.")
                    break
            for  k in range(0,len(df)):
                if df['id'][k] in st.session_state.Id:
                    df['Visited'][k]=1
                elif df['id'][k] in st.session_state.Bindex:
                    df['Blacklisted'][k]=1
            st.subheader("""
             Scroll Up to update and save your progress !

                 """)



    else:
        st.write("""

                 """)
