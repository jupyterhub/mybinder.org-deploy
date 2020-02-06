.. _mybinder-federation:

===========================
The mybinder.org Federation
===========================

The following table lists BinderHub deployments in the mybinder.org
federation, along with the status of each. For more information about
the BinderHub federation, who is in it, how to join it, etc, see
`the BinderHub federation page <https://binderhub.readthedocs.io/en/latest/federation/federation.html>`_.

==========================  ========  ===============  ==============  =============== =====
  URL                       Response  Docker registry  JupyterHub API  User/Build Pods Quota
==========================  ========  ===============  ==============  =============== =====
gke.mybinder.org
ovh.mybinder.org
gesis.mybinder.org
turing.mybinder.org
==========================  ========  ===============  ==============  =============== =====

.. raw:: html

   <script>
   var fedUrls = [
       "https://gke.mybinder.org",
       "https://ovh.mybinder.org",
       "https://gesis.mybinder.org",
       "https://turing.mybinder.org",
   ]

   // Use a dictionary to store the rows that should be updated
   var urlRows = {};
   fedUrls.forEach((url) => {
      document.querySelectorAll('tr').forEach((tr) => {
        if (tr.textContent.includes(url.replace('https://', ''))) {
           urlRows[url] = tr;
        };
      });
   });

   fedUrls.forEach((url) => {
       var urlHealth = url + '/health'
       var urlPrefix = url.split('//')[1].split('.')[0]

       // Query the endpoint and update health icon
       var row = urlRows[url];
       let [fieldUrl, fieldResponse, fieldRegistry, fieldHub, fieldPods, fieldQuota] = row.querySelectorAll('td')
       $.getJSON(urlHealth, {})
           .done((resp) => {
               if (resp['ok'] == false) {
                   setStatus(fieldResponse, 'fail')
               } else {
                   setStatus(fieldResponse, 'success')
               }

               let [respReg, respHub, respQuota] = resp['checks']

               if (respReg == false) {
                   setStatus(fieldRegistry, 'fail')
               } else {
                   setStatus(fieldRegistry, 'success')
               }

               if (respHub == false) {
                   setStatus(fieldHub, 'fail')
               } else {
                   setStatus(fieldHub, 'success')
               }

               fieldPods.textContent = `${respQuota['user_pods']}/${respQuota['build_pods']}`
               fieldQuota.textContent = `${respQuota['quota']}`
           })
           .fail((resp) => {
                setStatus(fieldResponse, 'fail')
       });
   })

   var setStatus = (td, kind) => {
      if (kind == "success") {
        td.textContent = "Success";
        td.style.color = "green";
      } else {
        td.textContent = "Fail";
        td.style.color = "red";
      }
   }

   </script>
