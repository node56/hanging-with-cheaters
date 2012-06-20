#! /usr/bin/perl -I~/lib/perl5 
use strict;
use CGI;
sub readWords {
  open(F,"< words.txt") || die;
  my @words;
  while(<F>) {
    chomp($_);
    push(@words, $_) if (length($_)>3);
  }
  return \@words;
}

sub bestGuess {
 my ($cs,$sr) = @_;
 my $rwords = &readWords();
 my $lv = $cs=~/.*([AIEOU])/ ? $1 : "Y";
 my $sofar = $cs;
 $sofar=~s/\.//g;
 $sofar.=$sr;
 my @poss = &getPoss($cs, $lv, $sofar, $rwords);
 return &figure($sofar, \@poss);
}

sub getPoss {
  my ($p, $lv, $sofar, $rwords) = @_;
  $p=~s/$lv(\.+)$/$lv. ("[^AEIOU$sofar]" x length($1))/e;
  $p=~s/\./[^$sofar]/g;
  return grep(/^$p$/, @$rwords);
}

sub bestWord {
 my ($ls) = @_;
  my $text;
  {
    local( $/, *FH ) ;
    open( FH, "<hwords") or die "sudden flaming death\n";
    $text = <FH>;
  }
  my @lines = ($text=~/\n([$ls]+ .*)/g);
  my %fs = {};
  for my $l (split(//, $ls)) {
    $fs{$l}++;
  }
  my @oks = grep(&ok($_, \%fs), @lines);
  return @oks;
}

sub oldWords {
  my ($ls) = @_;
  my %fs = {};
  for my $l (split(//, $ls)) {
    $fs{$l}++;
  }
  my $rwords = &readWords();
  my @cs = grep(&ok($_, \%fs), @$rwords);
  my @res;
  foreach my $w (@cs) {
    print ".";
    my $vowel = $w=~/.*([AEIOU])/ ? $1 : "Y";
    my $pat = $w;
    $pat=~s/[^$vowel]/./g;
    my @poss = &getPoss($pat, $vowel, $vowel, $rwords);
    my @stages = (scalar(@poss));
    my $total = scalar(@poss);
    my $i=0; 
    my $sofar = $vowel;
    while (scalar(@poss)>1) {
      my @guesses = &figure($sofar, \@poss);
      my ($guess, $count) = @{$guesses[0]};
      push(@stages, $count);
      $total += $count;
      $sofar .= $guess;
      my $p = $w;
      $p =~s/[^$sofar]/./g;
      @poss = &getPoss($p, $vowel, $sofar, \@poss);
      last if $i++>30;
    }
    push(@res,{"w",$w,"guesses",$sofar,"choices",\@stages,"total",$total});
  }
  return @res; 
}

sub figure {
  my ($sofar, $rp) =@_; 
  my %wcs;
  foreach my $pos (@$rp) {
    foreach my $l (split(//, $pos)) {
      $wcs{$l}++;
    }
  }
  
  my @res;
  foreach my $l (keys %wcs) {
    next if ($sofar=~/$l/);
    my $rctf = &cases($rp, $l.$sofar);
    my @ps = sort {scalar(@{$rctf->{$b}}) <=> scalar(@{$rctf->{$a}})} 
      keys %$rctf; 
    my $numPos = scalar(@{$rctf->{$ps[0]}});
    push(@res, [$l, $numPos, [@ps], $rctf]);
  }
  return sort {$a->[1]<=>$b->[1]} @res;
}

sub cases {
 my ($rp, $k) = @_;
 my %ctf;
 foreach my $p (@$rp) {
   my $a = $p;
   $a=~s/[^$k]/./g;
   push(@{$ctf{$a}}, $p);
 }
 return \%ctf;
}

sub maxCases {
 my ($rp, $k) = @_; 
 my $rctf = &cases($rp, $k);
 my $max = 0;
 foreach my $p (keys %$rctf) {
  my $l = scalar(@{$rctf->{$p}});
  if ($l>$max) { $max = $l; }
 }
 return $max;
}
 
sub getNextPoss {
 my ($rp, $w, $k)=@_;
 $w =~s/[^$k]/./g;
 my @haz = grep(/$w/, @$rp);
 return scalar(@haz);
}

sub ok {
 my ($l, $rfs) = @_;
 my ($w,$b) = split(/ /,$l,2);
 my @gs = split(//, $w);
 for my $l (@gs) { 
  return 0 unless ($rfs->{$l});
 }
 my %hs;
 for my $l (@gs) { 
  $hs{$l}++;
 }
 foreach my $l (keys %hs) {
   return 0 if ($hs{$l} > $rfs->{$l});
 }
 return 1;
}

my $q=CGI->new;
my $ls=uc($q->param('c'));
my $sofar=uc($q->param('s'));
my $who = $ENV{'REMOTE_ADDR'};
my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
my $time = sprintf("%04d%02d%02d%02d%02d%02d",$year+1900,$mon+1,$mday,$hour,$min,$sec);
if (open(F,">>log/hang.log")) {
  print F "connect\t",$time,"\t",$who,"\t",$ls,"\n";
  close(F);
}
print "Content-Type: text/html\n\n";

print "<html><head><title>Hanging With Cheaters</title></head>";
print "<body><pre><form><input type='text' name='c' value='$ls'/>";
print "<input type='submit'/></form>";
$|=1;
if ($ls=~/\./) { 
  my $url="hang.cgi?c=".$ls."&s=".$sofar;
  foreach my $res (&bestGuess($ls,$sofar)) { 
    my $l = $res->[0];
    my $rctf = $res->[3];
    print "<b>$l</b><table>";
    foreach my $p (@{$res->[2]}) {
      print "<tr><td align='right'>".scalar(@{$rctf->{$p}})."</td><td>".
       "<a href='hang.cgi?c=$p&s=$sofar$l'>$p</a></td></tr>\n";
    }
    print "</table>\n";
  }
}
elsif (length($ls)) {
  my @ress = &bestWord($ls);
  foreach my $res (@ress) {
    $res=~s/(\d+)/ $1 /g;
    print $res,"\n";
  }
}
print "</pre></body></html>\n";
