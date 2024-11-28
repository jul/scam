    <form  action=/user >
        <input type=number name=id />
        <input type=file name=pic_file />
        <input type=text name=name nullable=false unique=true />
        <input type=email name=email unique=true nullable=false />
        <input type=uuid name=secret_token nullable=true />
        <input type=password name=secret_password nullable=false />
    </form>
    <form action=/comment >
        <%include file="item.mako" />
        <%include file="category.mako" args='category="category"'  />
        <input type=datetime-local name=created_at_time default=func.now() class=hidden />
    </form>
    <form action=/transition >
        <input type=number name=id />
        <input type=number name=previous_comment_id reference=comment.id nullable=false />
        <input type=number name=next_comment_id reference=comment.id nullable=false />

    </form>
    <form action=/follower >
        <input type=number name=id />
        <input type=number name=followed_id reference=user.id nullable=false />
        <input type=number name=follower_id reference=user.id nullable=false >
    </form>
    <form action=/annexe_comment >
        <input type=number name=id />
        <input type=file name=annexe nullable=false />
        <input type=number name=comment_id reference=comment.id />
   </form>
   <form action=/like >
        <input type=number name=id />
        <input type=number name=user_id reference=user.id nullable=false />
        <input type=number name=comment_id reference=comment.id nullable=false />
   </form>
   <form action=/share >
        <input type=number name=id />
        <input type=number name=user_id reference=user.id nullable=false />
        <input type=number name=comment_id reference=comment.id nullable=false />
   </form>


