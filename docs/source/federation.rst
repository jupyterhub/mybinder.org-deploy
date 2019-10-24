===========================
The mybinder.org Federation
===========================

The following table lists BinderHub deployments in the mybinder.org
federation, along with the status of each.

================  ===
  URL
================  ===
gke.mybinder.org  ???
ovh.mybinder.org  ???
================  ===

.. raw:: html

   <script>
   var fedUrls = [
       "https://gke.mybinder.org",
       "https://ovh.mybinder.org",
   ]

   // Use a dictionary to store the fields that should be updated
   var urlFields = {};
   fedUrls.forEach((url) => {
      document.querySelectorAll('tr').forEach((tr) => {
        if (tr.textContent.includes(url.replace('https://', ''))) {
           urlFields[url] = tr.querySelectorAll('td')[1];
        };
      });
   });

   fedUrls.forEach((url) => {
       var urlHealth = url + '/health'
       var urlPrefix = url.split('//')[1].split('.')[0]

       // Query the endpoint and update health icon
       var field = urlFields[url];
       $.getJSON(urlHealth, {})
           .done((resp) => {
               if (resp['ok'] == false) {
                   setStatus(field, 'fail')
               } else {
                   setStatus(field, 'success')
               }
           })
           .fail((resp) => {
                setStatus(field, 'fail')
       });
   })

   var setStatus = (field, kind) => {
      if (kind == "success") {
        field.textContent = "Success";
        field.style.color = "green";
      } else {
        field.textContent = "Fail";
        field.style.color = "red";
      }
   }

   </script>