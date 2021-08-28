import pandas as pd
from math import cos, asin, sqrt
import streamlit as st
import base64

st.write("""
# Minimum Route for The SalesPerson
This app finds the **minimum route** that the sales person should follow inorder to minimize the travel cost , 
keeping in mind that he can travel to only 12 stores a day.

**NOTE :** The distance is calculated using **Haversine Formula** which may vary from the actual distance.

""")
st.write("""
         
    
        """)
Data = st.file_uploader("UPLOAD FILE -  larger files (>1000 rows) will take a few seconds for the algo to run", type={"csv"})
if Data is not None:
    df = pd.read_csv(Data)
else:
    df=pd.read_csv('shortened - Sheet1 (1).csv')

df['Marked']=0

st.sidebar.header('User Input Features')
view=['Minimal Route Finder','Visited','Blacklisted']
selected_view = st.sidebar.selectbox('View', view)

def load_data(view):
    if view=='Minimal Route Finder':
        return df[df['Blacklisted']==0]
    elif view=='Visited':
        return df[df['Visited']==1]
    else:
        return df[df['Blacklisted']==1]


def filedownload(df,filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    #filename = "minimalRoute_Day-"+user_day+".csv"
    href = f'<a href="data:file/csv;base64,{b64}" download={filename}>Download CSV File</a>'
    return href

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
    
    
    
elif selected_view=='Minimal Route Finder':

    sorted_unique_type = sorted(selected_data.Type.unique())
    selected_type = st.sidebar.multiselect('Type', sorted_unique_type, sorted_unique_type)
    
    sorted_unique_name = sorted(selected_data.Name.unique())
    selected_name = st.sidebar.multiselect('Blacklist Names', sorted_unique_name)
    st.sidebar.write('Do you really want to Blacklist the above stores ? Click on Yes .')
    if st.sidebar.button('Yes'):
        for i in range(0,len(df)):
            if df['Name'][i] in selected_name:
                df['Blacklisted'][i]=1
    
    # Filtering data
    df_selected_type = selected_data[(selected_data.Type.isin(selected_type)) & ~(selected_data.Name.isin(selected_name))]
    df_selected_type=df_selected_type.reset_index(drop=True)
    df_selected_type['Marked']=0
    
    def distance(lat1, lon1, lat2, lon2):
        p = 0.017453292519943295 # conversion to radians factor
        a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2  #a = haversine
        return 12742 * asin(sqrt(a))  #diameter of earth = 12742km
    
    
    #find the store closest to the current location
    
    def next(lat,lon):
        min_dist = 10000.0
        min_index=-1
        for i in range(0,len(df_selected_type)):
            if df_selected_type['Marked'][i]==0 & df_selected_type['Blacklisted'][i]==0 & df_selected_type['Visited'][i]==0:
                if distance(lat,lon,df_selected_type['Latitude'][i],df_selected_type['Longitude'][i]) < min_dist :
                    min_dist=distance(lat,lon,df_selected_type['Latitude'][i],df_selected_type['Longitude'][i])
                    min_index=i
                    if min_dist==0.0:
                        return min_index
        return min_index
    st.write("""
    
                 """)
    st.header('Enter coordinates of your starting point')    
    lat_input = 13.945281
    latitude = st.text_area("Latitude input", lat_input, height=25)
    
    st.write("""
    
    """)
    
    lon_input = 77.7364
    longitude = st.text_area("longitude input", lon_input, height=25)
    
    #latitude  =13.945281
    #longitude=77.7364
    # display the index of the next 12 stores that he should go to
    d = pd.DataFrame()
    for day in range(1,(len(df_selected_type)//12)+2):
        
        ind=[]
        lat=float(latitude)
        lon=float(longitude)
        index=next(lat,lon)
        
        while len(ind) != 12 and index !=-1:
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
    st.write("Origin( " +str(latitude) + " , " + str(longitude) +" )")
    
    #user_day='2'
    #day=2
    st.header('OUTPUT (The Minimum Route)')
    if(len(df_selected_type)>0):
            display = pd.DataFrame()
            
            display=d[d['Visited']==0].copy()
            display=display.reset_index(drop=True)
            Id=[]
            for  j in range(0,12):
                if(j<len(display)):
                   Id.append(int(display['ID'][j]))
            cols=['Address', 'Company Name', 'Distance', 'Link', 'Phone','Pin Code']
            st.dataframe(display[cols][0:12])
            st.markdown(filedownload(display,"Minimal_Route.csv"), unsafe_allow_html=True)
            st.subheader("Detailed trip info -")
            for i in range (0,12):
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
                if df['id'][k] in Id:
                    df['Visited'][k]=1
            st.header("""
                      
                      
                     Download The Complete Dataset Below !    
             """)
            st.write("DO NOT make any changes to this file !!")
            st.write('Data Dimension: ' + str(df.shape[0]) + ' rows and ' + str(df.shape[1]) + ' columns.')
            st.dataframe(df)
            st.markdown(filedownload(df,"Complete_Dataset.csv"), unsafe_allow_html=True)
            
    
    else:
        st.write("""
    
                 """)

