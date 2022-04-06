button_new_sh = document.getElementById("btn-new-share-dir");
button_new_sh.onclick = function add_new_sh(){
    document.getElementById("shared-dirs").innerHTML += `
    <div class="shared-dir">
        <form  method="post" action="/ns" class="shared-form">
        <div class="fields">        
                <div class="input-block">
                    <input name="path" class="input" type="text" name="path" placeholder="Folder path">                
                </div>  
                <div class="input-block">
                    <input name="users" class="input" type="text" name="users" placeholder="Allow users">
                </div> 
            </div>     
            <div class="change-form"> 
                <input type="submit" class="button btn-action btn-save" value="Save">  
            </div>         
        </form>           
    </div>`
}
